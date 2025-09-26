"""
工具函数模块
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json
import pandas as pd
import numpy as np

def setup_logger(name: str) -> logging.Logger:
    """设置日志记录器"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """获取日志记录器"""
    return setup_logger(name)

def ensure_directory(path: Path) -> Path:
    """确保目录存在"""
    path.mkdir(parents=True, exist_ok=True)
    return path

def save_json(data: dict, file_path: Path) -> bool:
    """保存JSON数据到文件"""
    try:
        ensure_directory(file_path.parent)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        return True
    except Exception as e:
        logging.error(f"保存JSON文件失败: {e}")
        return False

def load_json(file_path: Path) -> Optional[dict]:
    """从文件加载JSON数据"""
    try:
        if not file_path.exists():
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"加载JSON文件失败: {e}")
        return None

def format_timestamp(timestamp: datetime) -> str:
    """格式化时间戳"""
    return timestamp.strftime('%Y-%m-%d %H:%M:%S')

def format_number(number: float, decimals: int = 2) -> str:
    """格式化数字"""
    return f"{number:,.{decimals}f}"

def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """安全除法"""
    try:
        return a / b if b != 0 else default
    except (TypeError, ZeroDivisionError):
        return default

def calculate_percentage(value: float, total: float) -> float:
    """计算百分比"""
    return safe_divide(value * 100, total, 0.0)

def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> tuple[bool, str]:
    """验证密码强度"""
    if len(password) < 6:
        return False, "密码长度不能少于6位"
    
    if len(password) > 50:
        return False, "密码长度不能超过50位"
    
    if not any(c.isupper() for c in password):
        return False, "密码必须包含大写字母"
    
    if not any(c.islower() for c in password):
        return False, "密码必须包含小写字母"
    
    if not any(c.isdigit() for c in password):
        return False, "密码必须包含数字"
    
    return True, "密码强度符合要求"

def truncate_string(text: str, max_length: int = 100) -> str:
    """截断字符串"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def generate_random_string(length: int = 8) -> str:
    """生成随机字符串"""
    import random
    import string
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def hash_string(text: str) -> str:
    """哈希字符串"""
    import hashlib
    return hashlib.sha256(text.encode()).hexdigest()

def is_port_available(port: int) -> bool:
    """检查端口是否可用"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            return result != 0
    except Exception:
        return False

def calculate_financial_metrics(equity_curve: list, risk_free_rate: float = 0.02) -> Dict[str, float]:
    """计算金融指标"""
    if len(equity_curve) < 2:
        return {
            "total_return": 0.0,
            "annualized_return": 0.0,
            "volatility": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "calmar_ratio": 0.0
        }
    
    # 计算收益率
    returns = []
    for i in range(1, len(equity_curve)):
        ret = (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1]
        returns.append(ret)
    
    # 总收益率
    total_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0]
    
    # 年化收益率
    days = len(equity_curve)
    annualized_return = (1 + total_return) ** (365 / days) - 1
    
    # 波动率
    volatility = np.std(returns) * np.sqrt(365)
    
    # 夏普比率
    sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0
    
    # 最大回撤
    peak = equity_curve[0]
    max_drawdown = 0
    for value in equity_curve:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak
        max_drawdown = max(max_drawdown, drawdown)
    
    # 卡尔马比率
    calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0
    
    return {
        "total_return": total_return,
        "annualized_return": annualized_return,
        "volatility": volatility,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": max_drawdown,
        "calmar_ratio": calmar_ratio
    }

def format_currency(amount: float, currency: str = "USD") -> str:
    """格式化货币"""
    if currency == "USD":
        return f"${amount:,.2f}"
    elif currency == "CNY":
        return f"¥{amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """格式化百分比"""
    return f"{value:.{decimals}%}"

def calculate_position_size(
    account_balance: float,
    risk_per_trade: float,
    entry_price: float,
    stop_loss_price: Optional[float] = None
) -> float:
    """计算仓位大小"""
    if stop_loss_price and stop_loss_price > 0:
        # 基于止损的仓位计算
        risk_per_share = abs(entry_price - stop_loss_price)
        position_size = (account_balance * risk_per_trade) / risk_per_share
    else:
        # 基于固定百分比的仓位计算
        position_size = account_balance * risk_per_trade
    
    return max(0, position_size)

def calculate_stop_loss(
    entry_price: float,
    stop_loss_percent: float,
    trade_type: str = "long"
) -> float:
    """计算止损价格"""
    if trade_type.lower() == "long":
        return entry_price * (1 - stop_loss_percent)
    else:
        return entry_price * (1 + stop_loss_percent)

def calculate_take_profit(
    entry_price: float,
    take_profit_percent: float,
    trade_type: str = "long"
) -> float:
    """计算止盈价格"""
    if trade_type.lower() == "long":
        return entry_price * (1 + take_profit_percent)
    else:
        return entry_price * (1 - take_profit_percent)

def validate_trading_symbol(symbol: str) -> bool:
    """验证交易对格式"""
    import re
    # 基本的交易对格式检查
    pattern = r'^[A-Z0-9]{2,20}/[A-Z]{3,4}$|^[A-Z0-9]{2,20}[A-Z]{3,4}$'
    return re.match(pattern, symbol) is not None

def parse_timeframe(timeframe: str) -> int:
    """解析时间周期为秒数"""
    timeframe = timeframe.lower()
    if timeframe.endswith('m'):
        return int(timeframe[:-1]) * 60
    elif timeframe.endswith('h'):
        return int(timeframe[:-1]) * 3600
    elif timeframe.endswith('d'):
        return int(timeframe[:-1]) * 86400
    elif timeframe.endswith('w'):
        return int(timeframe[:-1]) * 604800
    else:
        return 3600  # 默认1小时

def generate_unique_id(prefix: str = "") -> str:
    """生成唯一ID"""
    import uuid
    unique_id = str(uuid.uuid4())
    return f"{prefix}_{unique_id}" if prefix else unique_id

def sanitize_filename(filename: str) -> str:
    """清理文件名"""
    import re
    # 移除非法字符
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # 替换空格为下划线
    filename = filename.replace(' ', '_')
    # 移除特殊字符
    filename = re.sub(r'[^\w\-_.]', '', filename)
    return filename

def compress_data(data: Any) -> bytes:
    """压缩数据"""
    import zlib
    import pickle
    return zlib.compress(pickle.dumps(data))

def decompress_data(compressed_data: bytes) -> Any:
    """解压缩数据"""
    import zlib
    import pickle
    return pickle.loads(zlib.decompress(compressed_data))