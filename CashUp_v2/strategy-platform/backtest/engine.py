"""
回测引擎 - 支持历史数据回测和性能分析
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass, asdict
import json
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

from ..strategies.base import StrategyBase, StrategyConfig, StrategySignal, BacktestResult
from ..data.manager import DataManager
from ..utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class BacktestConfig:
    """回测配置"""
    strategy_name: str
    strategy_class: type
    strategy_params: Dict[str, Any]
    symbols: List[str]
    timeframe: str
    start_date: datetime
    end_date: datetime
    initial_capital: float = 10000.0
    commission: float = 0.001
    slippage: float = 0.0005
    max_position_size: float = 1.0
    risk_per_trade: float = 0.02
    stop_loss: float = 0.05
    take_profit: float = 0.1
    
class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.results = {}
        self.current_backtest = None
        
    async def run_backtest(self, config: BacktestConfig) -> BacktestResult:
        """运行回测"""
        try:
            logger.info(f"开始回测: {config.strategy_name}")
            logger.info(f"回测期间: {config.start_date} - {config.end_date}")
            
            # 获取历史数据
            historical_data = await self.data_manager.get_historical_data(
                config.symbols,
                config.timeframe,
                config.start_date,
                config.end_date
            )
            
            if not historical_data:
                raise ValueError("无法获取历史数据")
            
            # 创建策略配置
            strategy_config = StrategyConfig(
                symbols=config.symbols,
                timeframe=config.timeframe,
                initial_capital=config.initial_capital,
                max_position_size=config.max_position_size,
                risk_per_trade=config.risk_per_trade,
                stop_loss=config.stop_loss,
                take_profit=config.take_profit,
                commission=config.commission,
                slippage=config.slippage,
                **config.strategy_params
            )
            
            # 创建策略实例
            strategy = config.strategy_class(strategy_config)
            strategy.initialize()
            
            # 执行回测
            result = await self._execute_backtest(strategy, historical_data, config)
            
            # 保存结果
            self.results[config.strategy_name] = result
            
            logger.info(f"回测完成: {config.strategy_name}")
            logger.info(f"总收益率: {result.total_return:.2%}")
            logger.info(f"夏普比率: {result.sharpe_ratio:.2f}")
            logger.info(f"最大回撤: {result.max_drawdown:.2%}")
            logger.info(f"胜率: {result.win_rate:.2%}")
            
            return result
            
        except Exception as e:
            logger.error(f"回测失败: {e}")
            raise
    
    async def _execute_backtest(
        self, 
        strategy: StrategyBase, 
        historical_data: Dict[str, pd.DataFrame],
        config: BacktestConfig
    ) -> BacktestResult:
        """执行回测"""
        
        # 初始化回测状态
        positions = {}
        cash = config.initial_capital
        equity = config.initial_capital
        trades = []
        equity_history = []
        drawdown_history = []
        
        # 合并所有symbol的数据
        all_data = []
        for symbol, data in historical_data.items():
            data = data.copy()
            data['symbol'] = symbol
            all_data.append(data)
        
        if not all_data:
            raise ValueError("没有可用的历史数据")
        
        # 按时间排序
        combined_data = pd.concat(all_data, ignore_index=True)
        combined_data = combined_data.sort_values('timestamp').reset_index(drop=True)
        
        # 逐个时间点处理
        for i, row in combined_data.iterrows():
            try:
                # 获取当前symbol的数据
                symbol = row['symbol']
                symbol_data = historical_data[symbol]
                
                # 获取当前时间点之前的数据
                current_time = row['timestamp']
                mask = symbol_data['timestamp'] <= current_time
                current_data = symbol_data[mask].copy()
                
                if len(current_data) < 2:  # 至少需要2个数据点
                    continue
                
                # 计算当前权益
                position_value = 0
                for pos_symbol, pos_amount in positions.items():
                    if pos_symbol == symbol:
                        current_price = row['close']
                        position_value += pos_amount * current_price
                
                equity = cash + position_value
                equity_history.append(equity)
                
                # 计算回撤
                if equity_history:
                    peak_equity = max(equity_history)
                    drawdown = (peak_equity - equity) / peak_equity
                    drawdown_history.append(drawdown)
                
                # 获取策略信号
                signal = strategy.on_data(current_data)
                
                if signal:
                    # 处理交易信号
                    trade_result = await self._process_signal(
                        signal, 
                        row, 
                        positions, 
                        cash, 
                        config
                    )
                    
                    if trade_result:
                        trades.append(trade_result)
                        cash = trade_result['cash_after']
                
            except Exception as e:
                logger.error(f"处理时间点 {row.get('timestamp', 'unknown')} 时出错: {e}")
                continue
        
        # 计算性能指标
        result = self._calculate_performance_metrics(
            trades, 
            equity_history, 
            drawdown_history, 
            config.initial_capital
        )
        
        return result
    
    async def _process_signal(
        self, 
        signal: StrategySignal, 
        market_data: pd.Series, 
        positions: Dict[str, float], 
        cash: float, 
        config: BacktestConfig
    ) -> Optional[Dict[str, Any]]:
        """处理交易信号"""
        
        symbol = signal.symbol
        current_price = market_data['close']
        
        # 计算实际成交价格（包含滑点）
        if signal.price:
            execution_price = signal.price * (1 + config.slippage)
        else:
            execution_price = current_price * (1 + config.slippage)
        
        # 计算交易成本
        trade_value = signal.quantity * execution_price
        commission = trade_value * config.commission
        
        trade_result = {
            'timestamp': market_data['timestamp'],
            'symbol': symbol,
            'signal_type': signal.signal_type.value,
            'quantity': signal.quantity,
            'price': execution_price,
            'commission': commission,
            'cash_before': cash,
            'cash_after': cash,
            'pnl': 0.0,
            'reason': signal.reason
        }
        
        if signal.signal_type.value == 'buy':
            # 买入信号
            total_cost = trade_value + commission
            
            if cash >= total_cost:
                # 执行买入
                positions[symbol] = positions.get(symbol, 0) + signal.quantity
                trade_result['cash_after'] = cash - total_cost
                trade_result['pnl'] = -commission
                
                logger.debug(f"买入 {symbol}: {signal.quantity} @ {execution_price}")
            else:
                logger.debug(f"资金不足，无法买入 {symbol}")
                return None
                
        elif signal.signal_type.value == 'sell':
            # 卖出信号
            if symbol in positions and positions[symbol] >= signal.quantity:
                # 执行卖出
                positions[symbol] -= signal.quantity
                trade_revenue = trade_value - commission
                trade_result['cash_after'] = cash + trade_revenue
                trade_result['pnl'] = trade_revenue - trade_value
                
                logger.debug(f"卖出 {symbol}: {signal.quantity} @ {execution_price}")
                
                # 如果仓位为0，移除symbol
                if positions[symbol] == 0:
                    del positions[symbol]
            else:
                logger.debug(f"仓位不足，无法卖出 {symbol}")
                return None
        
        return trade_result
    
    def _calculate_performance_metrics(
        self, 
        trades: List[Dict[str, Any]], 
        equity_history: List[float], 
        drawdown_history: List[float], 
        initial_capital: float
    ) -> BacktestResult:
        """计算性能指标"""
        
        result = BacktestResult()
        
        # 基本统计
        result.total_trades = len(trades)
        result.final_capital = equity_history[-1] if equity_history else initial_capital
        result.equity_curve = equity_history
        result.drawdown_curve = drawdown_history
        
        # 计算收益率
        if initial_capital > 0:
            result.total_return = (result.final_capital - initial_capital) / initial_capital
        
        # 计算交易统计
        if trades:
            # 盈利交易
            profitable_trades = [t for t in trades if t['pnl'] > 0]
            losing_trades = [t for t in trades if t['pnl'] < 0]
            
            result.profitable_trades = len(profitable_trades)
            result.win_rate = len(profitable_trades) / len(trades) if trades else 0
            
            # 平均盈利/亏损
            if profitable_trades:
                result.avg_win = sum(t['pnl'] for t in profitable_trades) / len(profitable_trades)
            if losing_trades:
                result.avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades)
            
            # 盈利因子
            total_profit = sum(t['pnl'] for t in profitable_trades)
            total_loss = abs(sum(t['pnl'] for t in losing_trades))
            result.profit_factor = total_profit / total_loss if total_loss > 0 else 0
        
        # 计算夏普比率
        if len(equity_history) > 1:
            returns = []
            for i in range(1, len(equity_history)):
                ret = (equity_history[i] - equity_history[i-1]) / equity_history[i-1]
                returns.append(ret)
            
            if returns:
                avg_return = sum(returns) / len(returns)
                return_std = np.std(returns)
                result.sharpe_ratio = avg_return / return_std if return_std > 0 else 0
        
        # 计算最大回撤
        if drawdown_history:
            result.max_drawdown = max(drawdown_history)
        
        result.trades = trades
        
        return result
    
    def generate_report(self, strategy_name: str, output_dir: str = "./reports") -> str:
        """生成回测报告"""
        if strategy_name not in self.results:
            raise ValueError(f"未找到策略 {strategy_name} 的回测结果")
        
        result = self.results[strategy_name]
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 生成图表
        self._plot_equity_curve(result, output_path / f"{strategy_name}_equity_curve.png")
        self._plot_drawdown_curve(result, output_path / f"{strategy_name}_drawdown_curve.png")
        self._plot_trade_distribution(result, output_path / f"{strategy_name}_trade_distribution.png")
        
        # 生成HTML报告
        report_path = output_path / f"{strategy_name}_report.html"
        self._generate_html_report(result, report_path)
        
        # 生成JSON报告
        json_path = output_path / f"{strategy_name}_report.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(result), f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"回测报告已生成: {report_path}")
        return str(report_path)
    
    def _plot_equity_curve(self, result: BacktestResult, output_path: Path):
        """绘制权益曲线"""
        plt.figure(figsize=(12, 6))
        
        if result.equity_curve:
            plt.plot(result.equity_curve, label='权益曲线', color='blue')
            plt.axhline(y=result.equity_curve[0], color='red', linestyle='--', label='初始资金')
            
            plt.title('权益曲线')
            plt.xlabel('时间')
            plt.ylabel('权益')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
    
    def _plot_drawdown_curve(self, result: BacktestResult, output_path: Path):
        """绘制回撤曲线"""
        plt.figure(figsize=(12, 6))
        
        if result.drawdown_curve:
            plt.fill_between(range(len(result.drawdown_curve)), 
                           result.drawdown_curve, 
                           color='red', 
                           alpha=0.3)
            plt.plot(result.drawdown_curve, color='red', linewidth=2)
            
            plt.title('回撤曲线')
            plt.xlabel('时间')
            plt.ylabel('回撤率')
            plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1%}'))
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
    
    def _plot_trade_distribution(self, result: BacktestResult, output_path: Path):
        """绘制交易分布"""
        if not result.trades:
            return
        
        plt.figure(figsize=(15, 10))
        
        # 子图1: PNL分布
        plt.subplot(2, 2, 1)
        pnls = [t['pnl'] for t in result.trades]
        plt.hist(pnls, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        plt.axvline(x=0, color='red', linestyle='--', linewidth=2)
        plt.title('PNL分布')
        plt.xlabel('PNL')
        plt.ylabel('频次')
        
        # 子图2: 累积PNL
        plt.subplot(2, 2, 2)
        cumulative_pnl = np.cumsum(pnls)
        plt.plot(cumulative_pnl, color='green', linewidth=2)
        plt.title('累积PNL')
        plt.xlabel('交易次数')
        plt.ylabel('累积PNL')
        plt.grid(True, alpha=0.3)
        
        # 子图3: 交易时间分布
        plt.subplot(2, 2, 3)
        if result.trades:
            trade_times = [t['timestamp'] for t in result.trades]
            plt.scatter(range(len(trade_times)), [t['pnl'] for t in result.trades], 
                       alpha=0.6, c=['green' if t['pnl'] > 0 else 'red' for t in result.trades])
            plt.title('交易时间分布')
            plt.xlabel('交易序号')
            plt.ylabel('PNL')
            plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # 子图4: 统计信息
        plt.subplot(2, 2, 4)
        plt.axis('off')
        
        stats_text = f"""
        总交易次数: {result.total_trades}
        盈利交易: {result.profitable_trades}
        胜率: {result.win_rate:.1%}
        平均盈利: {result.avg_win:.2f}
        平均亏损: {result.avg_loss:.2f}
        盈利因子: {result.profit_factor:.2f}
        最大回撤: {result.max_drawdown:.1%}
        夏普比率: {result.sharpe_ratio:.2f}
        """
        
        plt.text(0.1, 0.9, stats_text, transform=plt.gca().transAxes, 
                fontsize=12, verticalalignment='top', fontfamily='monospace')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _generate_html_report(self, result: BacktestResult, output_path: Path):
        """生成HTML报告"""
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>回测报告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .metrics {{ display: flex; flex-wrap: wrap; gap: 20px; margin: 20px 0; }}
                .metric {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; min-width: 200px; }}
                .metric h3 {{ margin: 0 0 10px 0; color: #333; }}
                .metric .value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
                .chart {{ margin: 20px 0; text-align: center; }}
                .chart img {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; }}
                .trades {{ margin: 20px 0; }}
                .trades table {{ width: 100%; border-collapse: collapse; }}
                .trades th, .trades td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .trades th {{ background-color: #f2f2f2; }}
                .profit {{ color: green; }}
                .loss {{ color: red; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>策略回测报告</h1>
                <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="metrics">
                <div class="metric">
                    <h3>总收益率</h3>
                    <div class="value">{result.total_return:.2%}</div>
                </div>
                <div class="metric">
                    <h3>夏普比率</h3>
                    <div class="value">{result.sharpe_ratio:.2f}</div>
                </div>
                <div class="metric">
                    <h3>最大回撤</h3>
                    <div class="value">{result.max_drawdown:.2%}</div>
                </div>
                <div class="metric">
                    <h3>胜率</h3>
                    <div class="value">{result.win_rate:.1%}</div>
                </div>
                <div class="metric">
                    <h3>总交易次数</h3>
                    <div class="value">{result.total_trades}</div>
                </div>
                <div class="metric">
                    <h3>最终资金</h3>
                    <div class="value">¥{result.final_capital:,.2f}</div>
                </div>
            </div>
            
            <div class="chart">
                <h2>权益曲线</h2>
                <img src="equity_curve.png" alt="权益曲线">
            </div>
            
            <div class="chart">
                <h2>回撤曲线</h2>
                <img src="drawdown_curve.png" alt="回撤曲线">
            </div>
            
            <div class="chart">
                <h2>交易分布</h2>
                <img src="trade_distribution.png" alt="交易分布">
            </div>
            
            <div class="trades">
                <h2>交易记录</h2>
                <table>
                    <thead>
                        <tr>
                            <th>时间</th>
                            <th>交易对</th>
                            <th>类型</th>
                            <th>数量</th>
                            <th>价格</th>
                            <th>手续费</th>
                            <th>PNL</th>
                            <th>原因</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # 添加交易记录
        for trade in result.trades[:20]:  # 只显示前20条
            pnl_class = "profit" if trade['pnl'] > 0 else "loss"
            html_content += f"""
                        <tr>
                            <td>{trade['timestamp']}</td>
                            <td>{trade['symbol']}</td>
                            <td>{trade['signal_type']}</td>
                            <td>{trade['quantity']}</td>
                            <td>{trade['price']:.4f}</td>
                            <td>{trade['commission']:.4f}</td>
                            <td class="{pnl_class}">{trade['pnl']:.2f}</td>
                            <td>{trade['reason']}</td>
                        </tr>
            """
        
        if len(result.trades) > 20:
            html_content += f"""
                        <tr>
                            <td colspan="8" style="text-align: center;">
                                还有 {len(result.trades) - 20} 条交易记录...
                            </td>
                        </tr>
            """
        
        html_content += """
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def compare_strategies(self, strategy_names: List[str]) -> pd.DataFrame:
        """比较多个策略的表现"""
        comparison_data = []
        
        for name in strategy_names:
            if name in self.results:
                result = self.results[name]
                comparison_data.append({
                    'Strategy': name,
                    'Total Return': f"{result.total_return:.2%}",
                    'Sharpe Ratio': f"{result.sharpe_ratio:.2f}",
                    'Max Drawdown': f"{result.max_drawdown:.2%}",
                    'Win Rate': f"{result.win_rate:.1%}",
                    'Total Trades': result.total_trades,
                    'Final Capital': f"¥{result.final_capital:,.2f}"
                })
        
        return pd.DataFrame(comparison_data)
    
    def get_results_summary(self) -> pd.DataFrame:
        """获取所有回测结果的摘要"""
        summary_data = []
        
        for name, result in self.results.items():
            summary_data.append({
                'Strategy': name,
                'Total Return': result.total_return,
                'Sharpe Ratio': result.sharpe_ratio,
                'Max Drawdown': result.max_drawdown,
                'Win Rate': result.win_rate,
                'Total Trades': result.total_trades,
                'Final Capital': result.final_capital
            })
        
        return pd.DataFrame(summary_data)