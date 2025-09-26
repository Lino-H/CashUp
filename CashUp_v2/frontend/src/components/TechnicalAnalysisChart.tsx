/**
 * 技术分析图表组件
 * Technical Analysis Chart Component
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Row,
  Col,
  Select,
  Radio,
  Button,
  Space,
  Alert,
  Typography,
  Spin,
  Tooltip,
  Divider,
  Checkbox,
} from 'antd';
import {
  LineChartOutlined,
  BarChartOutlined,
  AreaChartOutlined,
  PieChartOutlined,
  SettingOutlined,
  ReloadOutlined,
  DownloadOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  AreaChart,
  Area,
  ComposedChart,
  Scatter,
  ReferenceLine,
  Brush,
  Legend,
} from 'recharts';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { Group: RadioGroup } = Radio;

export interface PriceData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface TechnicalIndicator {
  ma5?: number;
  ma10?: number;
  ma20?: number;
  ma50?: number;
  macd?: number;
  signal?: number;
  histogram?: number;
  rsi?: number;
  kdj_k?: number;
  kdj_d?: number;
  kdj_j?: number;
  bb_upper?: number;
  bb_middle?: number;
  bb_lower?: number;
}

export interface TechnicalAnalysisData extends PriceData {
  indicators: TechnicalIndicator;
}

interface TechnicalAnalysisChartProps {
  symbol: string;
  data: TechnicalAnalysisData[];
  loading?: boolean;
  onIndicatorChange?: (indicators: string[]) => void;
  onTimeframeChange?: (timeframe: string) => void;
}

const TechnicalAnalysisChart: React.FC<TechnicalAnalysisChartProps> = ({
  symbol,
  data,
  loading = false,
  onIndicatorChange,
  onTimeframeChange,
}) => {
  const [selectedIndicators, setSelectedIndicators] = useState<string[]>(['ma20', 'macd', 'rsi']);
  const [timeframe, setTimeframe] = useState<string>('1d');
  const [chartType, setChartType] = useState<'line' | 'candlestick' | 'volume'>('line');
  const [showVolume, setShowVolume] = useState<boolean>(true);

  // 技术指标配置
  const indicatorConfig = {
    ma5: { color: '#ff6b6b', name: 'MA5', type: 'trend' },
    ma10: { color: '#4ecdc4', name: 'MA10', type: 'trend' },
    ma20: { color: '#45b7d1', name: 'MA20', type: 'trend' },
    ma50: { color: '#96ceb4', name: 'MA50', type: 'trend' },
    macd: { color: '#feca57', name: 'MACD', type: 'momentum' },
    signal: { color: '#ff9ff3', name: 'Signal', type: 'momentum' },
    histogram: { color: '#54a0ff', name: 'Histogram', type: 'momentum' },
    rsi: { color: '#5f27cd', name: 'RSI', type: 'momentum' },
    kdj_k: { color: '#00d2d3', name: 'K', type: 'oscillator' },
    kdj_d: { color: '#ff9ff3', name: 'D', type: 'oscillator' },
    kdj_j: { color: '#feca57', name: 'J', type: 'oscillator' },
    bb_upper: { color: '#ff6b6b', name: 'BB Upper', type: 'volatility' },
    bb_middle: { color: '#45b7d1', name: 'BB Middle', type: 'volatility' },
    bb_lower: { color: '#96ceb4', name: 'BB Lower', type: 'volatility' },
  };

  // 时间周期选项
  const timeframeOptions = [
    { value: '1m', label: '1分钟' },
    { value: '5m', label: '5分钟' },
    { value: '15m', label: '15分钟' },
    { value: '1h', label: '1小时' },
    { value: '4h', label: '4小时' },
    { value: '1d', label: '1天' },
    { value: '1w', label: '1周' },
    { value: '1M', label: '1月' },
  ];

  // 指标分组
  const indicatorGroups = {
    trend: ['ma5', 'ma10', 'ma20', 'ma50'],
    momentum: ['macd', 'signal', 'histogram', 'rsi'],
    oscillator: ['kdj_k', 'kdj_d', 'kdj_j'],
    volatility: ['bb_upper', 'bb_middle', 'bb_lower'],
  };

  // 处理指标选择
  const handleIndicatorChange = useCallback((indicator: string, checked: boolean) => {
    const updatedIndicators = checked
      ? [...selectedIndicators, indicator]
      : selectedIndicators.filter(i => i !== indicator);
    
    setSelectedIndicators(updatedIndicators);
    onIndicatorChange?.(updatedIndicators);
  }, [selectedIndicators, onIndicatorChange]);

  // 处理时间周期变化
  const handleTimeframeChange = useCallback((value: string) => {
    setTimeframe(value);
    onTimeframeChange?.(value);
  }, [onTimeframeChange]);

  // 渲染K线图
  const renderCandlestickChart = () => {
    return (
      <ComposedChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="timestamp" 
          tickFormatter={(value) => new Date(value).toLocaleDateString()}
        />
        <YAxis />
        <RechartsTooltip />
        <Legend />
        
        {/* 价格蜡烛图 */}
        <Bar dataKey="close" fill="#8884d8" />
        
        {/* 移动平均线 */}
        {selectedIndicators.includes('ma20') && (
          <Line 
            type="monotone" 
            dataKey="indicators.ma20" 
            stroke={indicatorConfig.ma20.color}
            name="MA20"
          />
        )}
        
        {selectedIndicators.includes('ma50') && (
          <Line 
            type="monotone" 
            dataKey="indicators.ma50" 
            stroke={indicatorConfig.ma50.color}
            name="MA50"
          />
        )}
      </ComposedChart>
    );
  };

  // 渲染价格线图
  const renderPriceChart = () => {
    return (
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="timestamp" 
          tickFormatter={(value) => new Date(value).toLocaleDateString()}
        />
        <YAxis />
        <RechartsTooltip />
        <Legend />
        
        {/* 价格线 */}
        <Line 
          type="monotone" 
          dataKey="close" 
          stroke="#1890ff" 
          strokeWidth={2}
          name="价格"
        />
        
        {/* 移动平均线 */}
        {selectedIndicators.includes('ma5') && (
          <Line 
            type="monotone" 
            dataKey="indicators.ma5" 
            stroke={indicatorConfig.ma5.color}
            name="MA5"
          />
        )}
        
        {selectedIndicators.includes('ma10') && (
          <Line 
            type="monotone" 
            dataKey="indicators.ma10" 
            stroke={indicatorConfig.ma10.color}
            name="MA10"
          />
        )}
        
        {selectedIndicators.includes('ma20') && (
          <Line 
            type="monotone" 
            dataKey="indicators.ma20" 
            stroke={indicatorConfig.ma20.color}
            name="MA20"
          />
        )}
        
        {selectedIndicators.includes('ma50') && (
          <Line 
            type="monotone" 
            dataKey="indicators.ma50" 
            stroke={indicatorConfig.ma50.color}
            name="MA50"
          />
        )}
      </LineChart>
    );
  };

  // 渲染成交量图
  const renderVolumeChart = () => {
    return (
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="timestamp" 
          tickFormatter={(value) => new Date(value).toLocaleDateString()}
        />
        <YAxis />
        <RechartsTooltip />
        <Bar dataKey="volume" fill="#52c41a" />
      </BarChart>
    );
  };

  // 渲染MACD指标
  const renderMACDChart = () => {
    return (
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="timestamp" 
          tickFormatter={(value) => new Date(value).toLocaleDateString()}
        />
        <YAxis />
        <RechartsTooltip />
        <Legend />
        
        {selectedIndicators.includes('macd') && (
          <Line 
            type="monotone" 
            dataKey="indicators.macd" 
            stroke={indicatorConfig.macd.color}
            name="MACD"
          />
        )}
        
        {selectedIndicators.includes('signal') && (
          <Line 
            type="monotone" 
            dataKey="indicators.signal" 
            stroke={indicatorConfig.signal.color}
            name="Signal"
          />
        )}
        
        {selectedIndicators.includes('histogram') && (
          <Line 
            type="monotone" 
            dataKey="indicators.histogram" 
            stroke={indicatorConfig.histogram.color}
            name="Histogram"
          />
        )}
      </LineChart>
    );
  };

  // 渲染RSI指标
  const renderRSIChart = () => {
    return (
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="timestamp" 
          tickFormatter={(value) => new Date(value).toLocaleDateString()}
        />
        <YAxis domain={[0, 100]} />
        <RechartsTooltip />
        <Legend />
        
        {selectedIndicators.includes('rsi') && (
          <Line 
            type="monotone" 
            dataKey="indicators.rsi" 
            stroke={indicatorConfig.rsi.color}
            name="RSI"
          />
        )}
        
        {/* RSI 超买超卖线 */}
        <ReferenceLine y={70} stroke="#ff4d4f" strokeDasharray="5 5" />
        <ReferenceLine y={30} stroke="#52c41a" strokeDasharray="5 5" />
      </LineChart>
    );
  };

  // 渲染布林带
  const renderBollingerBandsChart = () => {
    return (
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="timestamp" 
          tickFormatter={(value) => new Date(value).toLocaleDateString()}
        />
        <YAxis />
        <RechartsTooltip />
        <Legend />
        
        {/* 布林带 */}
        {selectedIndicators.includes('bb_upper') && (
          <Line 
            type="monotone" 
            dataKey="indicators.bb_upper" 
            stroke={indicatorConfig.bb_upper.color}
            name="BB Upper"
          />
        )}
        
        {selectedIndicators.includes('bb_middle') && (
          <Line 
            type="monotone" 
            dataKey="indicators.bb_middle" 
            stroke={indicatorConfig.bb_middle.color}
            name="BB Middle"
          />
        )}
        
        {selectedIndicators.includes('bb_lower') && (
          <Line 
            type="monotone" 
            dataKey="indicators.bb_lower" 
            stroke={indicatorConfig.bb_lower.color}
            name="BB Lower"
          />
        )}
        
        {/* 价格线 */}
        <Line 
          type="monotone" 
          dataKey="close" 
          stroke="#1890ff" 
          strokeWidth={2}
          name="价格"
        />
      </LineChart>
    );
  };

  // 渲染KDJ指标
  const renderKDJChart = () => {
    return (
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="timestamp" 
          tickFormatter={(value) => new Date(value).toLocaleDateString()}
        />
        <YAxis domain={[0, 100]} />
        <RechartsTooltip />
        <Legend />
        
        {selectedIndicators.includes('kdj_k') && (
          <Line 
            type="monotone" 
            dataKey="indicators.kdj_k" 
            stroke={indicatorConfig.kdj_k.color}
            name="K"
          />
        )}
        
        {selectedIndicators.includes('kdj_d') && (
          <Line 
            type="monotone" 
            dataKey="indicators.kdj_d" 
            stroke={indicatorConfig.kdj_d.color}
            name="D"
          />
        )}
        
        {selectedIndicators.includes('kdj_j') && (
          <Line 
            type="monotone" 
            dataKey="indicators.kdj_j" 
            stroke={indicatorConfig.kdj_j.color}
            name="J"
          />
        )}
      </LineChart>
    );
  };

  // 获取当前渲染的图表
  const renderChart = () => {
    if (loading) {
      return (
        <div style={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Spin size="large" />
        </div>
      );
    }

    switch (chartType) {
      case 'candlestick':
        return renderCandlestickChart();
      case 'line':
      default:
        return renderPriceChart();
    }
  };

  // 渲染指标面板
  const renderIndicatorPanel = () => {
    return (
      <div style={{ marginBottom: 20 }}>
        <Title level={4}>技术指标</Title>
        <Row gutter={[16, 16]}>
          {Object.entries(indicatorGroups).map(([group, indicators]) => (
            <Col span={6} key={group}>
              <Card size="small" title={group}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  {indicators.map(indicator => (
                    <Checkbox
                      key={indicator}
                      checked={selectedIndicators.includes(indicator)}
                      onChange={(e) => handleIndicatorChange(indicator, e.target.checked)}
                    >
                      <Text style={{ color: indicatorConfig[indicator].color }}>
                        {indicatorConfig[indicator].name}
                      </Text>
                    </Checkbox>
                  ))}
                </Space>
              </Card>
            </Col>
          ))}
        </Row>
      </div>
    );
  };

  return (
    <div style={{ padding: 24 }}>
      {/* 标题和控制 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={16}>
          <Title level={3}>技术分析 - {symbol}</Title>
          <Paragraph type="secondary">
            专业技术分析图表，包含多种技术指标和工具
          </Paragraph>
        </Col>
        <Col span={8} style={{ textAlign: 'right' }}>
          <Space>
            <Select
              value={timeframe}
              onChange={handleTimeframeChange}
              style={{ width: 100 }}
            >
              {timeframeOptions.map(option => (
                <Option key={option.value} value={option.value}>
                  {option.label}
                </Option>
              ))}
            </Select>
            
            <RadioGroup 
              value={chartType} 
              onChange={(e) => setChartType(e.target.value as any)}
              size="small"
            >
              <Radio.Button value="line">线图</Radio.Button>
              <Radio.Button value="candlestick">K线</Radio.Button>
              <Radio.Button value="volume">成交量</Radio.Button>
            </RadioGroup>
            
            <Button icon={<ReloadOutlined />} size="small">
              刷新
            </Button>
            
            <Button icon={<DownloadOutlined />} size="small">
              导出
            </Button>
          </Space>
        </Col>
      </Row>

      {/* 指标面板 */}
      {renderIndicatorPanel()}

      {/* 主图表 */}
      <Card title="价格图表" style={{ marginBottom: 16 }}>
        <ResponsiveContainer width="100%" height={400}>
          {renderChart()}
        </ResponsiveContainer>
      </Card>

      {/* 技术指标图表 */}
      <Row gutter={[16, 16]}>
        {selectedIndicators.includes('macd') && (
          <Col span={12}>
            <Card title="MACD">
              <ResponsiveContainer width="100%" height={200}>
                {renderMACDChart()}
              </ResponsiveContainer>
            </Card>
          </Col>
        )}
        
        {selectedIndicators.includes('rsi') && (
          <Col span={12}>
            <Card title="RSI">
              <ResponsiveContainer width="100%" height={200}>
                {renderRSIChart()}
              </ResponsiveContainer>
            </Card>
          </Col>
        )}
        
        {selectedIndicators.includes('bb_upper') && (
          <Col span={12}>
            <Card title="布林带">
              <ResponsiveContainer width="100%" height={200}>
                {renderBollingerBandsChart()}
              </ResponsiveContainer>
            </Card>
          </Col>
        )}
        
        {selectedIndicators.includes('kdj_k') && (
          <Col span={12}>
            <Card title="KDJ">
              <ResponsiveContainer width="100%" height={200}>
                {renderKDJChart()}
              </ResponsiveContainer>
            </Card>
          </Col>
        )}
      </Row>

      {/* 使用说明 */}
      <Card title="技术分析说明" style={{ marginTop: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Alert
            message="趋势指标"
            description="移动平均线(MA)用于识别价格趋势方向，短期均线反映近期走势，长期均线反映长期趋势。"
            type="info"
            showIcon
          />
          
          <Alert
            message="动量指标"
            description="MACD通过快慢均线差值判断市场动量，RSI通过相对强弱判断超买超卖状态。"
            type="warning"
            showIcon
          />
          
          <Alert
            message="震荡指标"
            description="KDJ通过最高价、最低价和收盘价计算，判断价格的超买超卖状态。"
            type="success"
            showIcon
          />
          
          <Alert
            message="波动率指标"
            description="布林带通过标准差计算价格通道，价格突破上下轨可能预示趋势变化。"
            type="error"
            showIcon
          />
        </Space>
      </Card>
    </div>
  );
};

export default TechnicalAnalysisChart;