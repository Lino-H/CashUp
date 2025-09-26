/**
 * 风险分析组件
 * Risk Analysis Component
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Typography,
  Space,
  Alert,
  Progress,
  Tag,
  Badge,
  Button,
  Select,
  Radio,
  Switch,
  Input,
  Slider,
  Divider,
  List,
  Table,
  Modal,
  Form,
  Tooltip,
  Avatar,
  Rate,
  Calendar,
  Tabs,
  Spin,
  message,
} from 'antd';
import {
  WarningOutlined,
  ExclamationCircleOutlined,
  SafetyOutlined,
  SafetyCertificateOutlined,
  FireOutlined,
  ThunderboltOutlined,
  DashboardOutlined,
  LineChartOutlined,
  BarChartOutlined,
  PieChartOutlined,
  AlertOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  InfoCircleOutlined,
  EyeOutlined,
  EditOutlined,
  SettingOutlined,
  BellOutlined,
  TrophyOutlined,
  BulbOutlined,
  AuditOutlined,
  BankOutlined,
  StockOutlined,
  DollarOutlined,
  GlobalOutlined,
  RocketOutlined,
  HeartOutlined,
  ShareAltOutlined,
  TagOutlined,
  EnvironmentOutlined,
  TeamOutlined,
  ClockCircleOutlined,
  PercentageOutlined,
  HomeOutlined,
  BankOutlined as BanknoteOutlined,
  RocketOutlined as RocketLaunchOutlined,
  AntDesignOutlined,
  FundOutlined,
  FundProjectionScreenOutlined,
  StockOutlined as StockOutlined2,
  WarningOutlined as WarningFilledOutlined,
} from '@ant-design/icons';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  ComposedChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ScatterChart,
  Scatter,
} from 'recharts';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const RadioGroup = Radio.Group;
const { TabPane } = Tabs;

// 风险数据类型定义
export interface RiskData {
  timestamp: number;
  portfolioVaR: number;
  positionVaR: number;
  marketRisk: number;
  creditRisk: number;
  liquidityRisk: number;
  operationalRisk: number;
  overallRisk: number;
  stressTest: number;
}

export interface PositionRisk {
  symbol: string;
  positionSize: number;
  currentPrice: number;
  dailyPnL: number;
  riskScore: number;
  VaR: number;
  beta: number;
  correlation: number;
  concentrationRisk: number;
  stopLoss: number;
  takeProfit: number;
}

export interface RiskAlert {
  id: string;
  type: 'warning' | 'error' | 'info';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  timestamp: number;
  acknowledged: boolean;
  category: 'market' | 'position' | 'portfolio' | 'system';
}

// API调用函数
const fetchRiskData = async (portfolioId: string, timeframe: string): Promise<RiskData[]> => {
  // 这里应该调用真实的风险分析API
  throw new Error('风险数据API尚未实现');
};

const fetchPositionRisk = async (portfolioId: string): Promise<PositionRisk[]> => {
  // 这里应该调用真实的持仓风险API
  throw new Error('持仓风险API尚未实现');
};

const fetchRiskAlerts = async (portfolioId: string): Promise<RiskAlert[]> => {
  // 这里应该调用真实的风险警报API
  throw new Error('风险警报API尚未实现');
};

// 风险颜色映射
const getRiskColor = (risk: number): string => {
  if (risk > 0.8) return '#f5222d'; // 高风险 - 红色
  if (risk > 0.6) return '#fa8c16'; // 中高风险 - 橙色
  if (risk > 0.4) return '#faad14'; // 中等风险 - 黄色
  if (risk > 0.2) return '#52c41a'; // 低风险 - 绿色
  return '#1890ff'; // 很低风险 - 蓝色
};

// 风险等级描述
const getRiskLevel = (risk: number): string => {
  if (risk > 0.8) return '高风险';
  if (risk > 0.6) return '中高风险';
  if (risk > 0.4) return '中等风险';
  if (risk > 0.2) return '低风险';
  return '很低风险';
};

// 风险警报颜色
const getAlertColor = (severity: string): string => {
  switch (severity) {
    case 'critical': return '#f5222d';
    case 'high': return '#fa8c16';
    case 'medium': return '#faad14';
    case 'low': return '#52c41a';
    default: return '#1890ff';
  }
};

// 风险警报类型图标
const getAlertIcon = (type: string): React.ReactNode => {
  switch (type) {
    case 'error': return <CloseCircleOutlined />;
    case 'warning': return <WarningOutlined />;
    case 'info': return <InfoCircleOutlined />;
    default: return <ExclamationCircleOutlined />;
  }
};

// 数据验证工具函数
const validateRiskData = (data: RiskData[]): RiskData[] => {
  return data.map(item => ({
    ...item,
    portfolioVaR: item.portfolioVaR || 0,
    marketRisk: item.marketRisk || 0,
    creditRisk: item.creditRisk || 0,
    liquidityRisk: item.liquidityRisk || 0,
    operationalRisk: item.operationalRisk || 0,
    overallRisk: item.overallRisk || 0,
    stressTest: item.stressTest || 0,
    positionVaR: item.positionVaR || 0,
  }));
};

interface RiskAnalysisProps {
  portfolioId?: string;
  timeframe?: string;
  autoRefresh?: boolean;
  onRiskChange?: (risk: RiskData) => void;
}

const RiskAnalysis: React.FC<RiskAnalysisProps> = ({
  portfolioId = 'default',
  timeframe = '1d',
  autoRefresh = true,
  onRiskChange,
}) => {
  const [riskData, setRiskData] = useState<RiskData[]>([]);
  const [positionRisk, setPositionRisk] = useState<PositionRisk[]>([]);
  const [riskAlerts, setRiskAlerts] = useState<RiskAlert[]>([]);
  const [selectedTimeframe, setSelectedTimeframe] = useState(timeframe);
  const [loading, setLoading] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [alertModalVisible, setAlertModalVisible] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState<RiskAlert | null>(null);

  // 初始化数据
  useEffect(() => {
    const initializeData = async () => {
      setLoading(true);
      try {
        const [riskDataResult, positionRiskResult, riskAlertsResult] = await Promise.allSettled([
          fetchRiskData(portfolioId, selectedTimeframe),
          fetchPositionRisk(portfolioId),
          fetchRiskAlerts(portfolioId)
        ]);
        
        if (riskDataResult.status === 'fulfilled') {
          setRiskData(riskDataResult.value);
          if (riskDataResult.value.length > 0) {
            onRiskChange?.(riskDataResult.value[riskDataResult.value.length - 1]);
          }
        } else {
          console.error('获取风险数据失败:', riskDataResult.reason);
          message.error(`风险数据加载失败: ${riskDataResult.reason.message}`);
        }
        
        if (positionRiskResult.status === 'fulfilled') {
          setPositionRisk(positionRiskResult.value);
        } else {
          console.error('获取持仓风险失败:', positionRiskResult.reason);
          message.error(`持仓风险数据加载失败: ${positionRiskResult.reason.message}`);
        }
        
        if (riskAlertsResult.status === 'fulfilled') {
          setRiskAlerts(riskAlertsResult.value);
        } else {
          console.error('获取风险警报失败:', riskAlertsResult.reason);
          message.error(`风险警报数据加载失败: ${riskAlertsResult.reason.message}`);
        }
      } catch (error) {
        console.error('初始化风险数据失败:', error);
      } finally {
        setLoading(false);
      }
    };

    initializeData();
  }, [portfolioId, selectedTimeframe]);

  // 自动刷新
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(async () => {
      try {
        const [riskDataResult, positionRiskResult, riskAlertsResult] = await Promise.allSettled([
          fetchRiskData(portfolioId, selectedTimeframe),
          fetchPositionRisk(portfolioId),
          fetchRiskAlerts(portfolioId)
        ]);
        
        if (riskDataResult.status === 'fulfilled') {
          setRiskData(riskDataResult.value);
          if (riskDataResult.value.length > 0) {
            onRiskChange?.(riskDataResult.value[riskDataResult.value.length - 1]);
          }
        }
        
        if (positionRiskResult.status === 'fulfilled') {
          setPositionRisk(positionRiskResult.value);
        }
        
        if (riskAlertsResult.status === 'fulfilled') {
          setRiskAlerts(riskAlertsResult.value);
        }
      } catch (error) {
        console.error('自动刷新风险数据失败:', error);
      }
    }, 30000); // 每30秒刷新一次

    return () => clearInterval(interval);
  }, [autoRefresh, onRiskChange, portfolioId, selectedTimeframe]);

  // 处理时间周期变化
  const handleTimeframeChange = useCallback(async (value: string) => {
    setSelectedTimeframe(value);
    setLoading(true);
    try {
      const newData = await fetchRiskData(portfolioId, value);
      setRiskData(newData);
    } catch (error) {
      console.error('获取新时间周期数据失败:', error);
    } finally {
      setLoading(false);
    }
  }, [portfolioId]);

  // 处理警报详情
  const handleAlertClick = useCallback((alert: RiskAlert) => {
    setSelectedAlert(alert);
    setAlertModalVisible(true);
  }, []);

  // 处理警报确认
  const handleAlertAcknowledge = useCallback((alertId: string) => {
    setRiskAlerts(prev => prev.map(alert => 
      alert.id === alertId ? { ...alert, acknowledged: true } : alert
    ));
    setAlertModalVisible(false);
    setSelectedAlert(null);
  }, []);

  // 渲染风险趋势图
  const renderRiskTrendChart = () => {
    if (loading) {
      return (
        <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Spin size="large" />
        </div>
      );
    }

    if (!riskData || riskData.length === 0) {
      return (
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <Alert message="暂无风险数据" type="info" />
        </div>
      );
    }
    
    // 确保数据字段存在
    const validatedData = validateRiskData(riskData);

    const latestData = validatedData[validatedData.length - 1];
    const chartData = validatedData.map(data => ({
      time: new Date(data.timestamp).toLocaleDateString(),
      portfolioVaR: (data.portfolioVaR || 0) * 100,
      marketRisk: (data.marketRisk || 0) * 100,
      creditRisk: (data.creditRisk || 0) * 100,
      liquidityRisk: (data.liquidityRisk || 0) * 100,
      overallRisk: (data.overallRisk || 0) * 100,
    }));

    return (
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis />
          <RechartsTooltip />
          <Area 
            type="monotone" 
            dataKey="portfolioVaR" 
            stroke="#1890ff" 
            fill="#1890ff" 
            fillOpacity={0.3}
            name="VaR"
          />
          <Area 
            type="monotone" 
            dataKey="marketRisk" 
            stroke="#52c41a" 
            fill="#52c41a" 
            fillOpacity={0.3}
            name="市场风险"
          />
          <Area 
            type="monotone" 
            dataKey="creditRisk" 
            stroke="#faad14" 
            fill="#faad14" 
            fillOpacity={0.3}
            name="信用风险"
          />
          <Area 
            type="monotone" 
            dataKey="liquidityRisk" 
            stroke="#fa8c16" 
            fill="#fa8c16" 
            fillOpacity={0.3}
            name="流动性风险"
          />
          <Line 
            type="monotone" 
            dataKey="overallRisk" 
            stroke="#f5222d" 
            strokeWidth={2}
            name="总体风险"
          />
        </ComposedChart>
      </ResponsiveContainer>
    );
  };

  // 渲染风险指标卡片
  const renderRiskMetrics = () => {
    if (!riskData.length || loading) return null;

    const validatedData = validateRiskData(riskData);
    
    const latestData = validatedData[validatedData.length - 1];

    return (
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card>
            <Statistic
              title="投资组合VaR"
              value={latestData.portfolioVaR * 100}
              suffix="%"
              valueStyle={{ color: getRiskColor(latestData.portfolioVaR) }}
              prefix={<DashboardOutlined />}
            />
            <Progress
              percent={latestData.portfolioVaR * 100}
              strokeColor={getRiskColor(latestData.portfolioVaR)}
              trailColor="#f0f0f0"
              showInfo={false}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="市场风险"
              value={latestData.marketRisk * 100}
              suffix="%"
              valueStyle={{ color: getRiskColor(latestData.marketRisk) }}
              prefix={<LineChartOutlined />}
            />
            <Progress
              percent={latestData.marketRisk * 100}
              strokeColor={getRiskColor(latestData.marketRisk)}
              trailColor="#f0f0f0"
              showInfo={false}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="信用风险"
              value={latestData.creditRisk * 100}
              suffix="%"
              valueStyle={{ color: getRiskColor(latestData.creditRisk) }}
              prefix={<BankOutlined />}
            />
            <Progress
              percent={latestData.creditRisk * 100}
              strokeColor={getRiskColor(latestData.creditRisk)}
              trailColor="#f0f0f0"
              showInfo={false}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="流动性风险"
              value={latestData.liquidityRisk * 100}
              suffix="%"
              valueStyle={{ color: getRiskColor(latestData.liquidityRisk) }}
              prefix={<DollarOutlined />}
            />
            <Progress
              percent={latestData.liquidityRisk * 100}
              strokeColor={getRiskColor(latestData.liquidityRisk)}
              trailColor="#f0f0f0"
              showInfo={false}
            />
          </Card>
        </Col>
      </Row>
    );
  };

  // 渲染持仓风险表格
  const renderPositionRiskTable = () => {
    if (!positionRisk.length || loading) return null;

    const columns = [
      {
        title: '交易对',
        dataIndex: 'symbol',
        key: 'symbol',
        render: (text: string) => <Text strong>{text}</Text>,
      },
      {
        title: '持仓数量',
        dataIndex: 'positionSize',
        key: 'positionSize',
        render: (text: number) => text.toFixed(4),
      },
      {
        title: '当前价格',
        dataIndex: 'currentPrice',
        key: 'currentPrice',
        render: (text: number) => `$${text.toFixed(2)}`,
      },
      {
        title: '日盈亏',
        dataIndex: 'dailyPnL',
        key: 'dailyPnL',
        render: (text: number) => (
          <span style={{ color: text >= 0 ? '#52c41a' : '#f5222d' }}>
            {text >= 0 ? '+' : ''}{text.toFixed(2)}
          </span>
        ),
      },
      {
        title: '风险评分',
        dataIndex: 'riskScore',
        key: 'riskScore',
        render: (text: number) => (
          <Progress
            percent={text}
            strokeColor={getRiskColor(text / 100)}
            trailColor="#f0f0f0"
            size={60}
            format={() => text.toFixed(0)}
          />
        ),
      },
      {
        title: 'VaR',
        dataIndex: 'VaR',
        key: 'VaR',
        render: (text: number) => `${(text * 100).toFixed(2)}%`,
      },
      {
        title: '操作',
        key: 'action',
        render: (_, record: PositionRisk) => (
          <Button type="link" size="small" onClick={() => handleAlertClick({
            id: `position_${record.symbol}`,
            type: 'warning',
            severity: 'medium',
            title: `${record.symbol} 持仓风险`,
            description: `持仓 ${record.symbol} 的风险评分为 ${record.riskScore.toFixed(1)}`,
            timestamp: Date.now(),
            acknowledged: false,
            category: 'position',
          })}>
            详情
          </Button>
        ),
      },
    ];

    return (
      <Card title="持仓风险分析" style={{ marginBottom: 16 }}>
        <Table
          dataSource={positionRisk}
          columns={columns}
          rowKey="symbol"
          pagination={false}
          size="small"
        />
      </Card>
    );
  };

  // 渲染风险警报列表
  const renderRiskAlerts = () => {
    if (!riskAlerts.length || loading) return null;

    const columns = [
      {
        title: '警报类型',
        dataIndex: 'type',
        key: 'type',
        render: (type: string, record: RiskAlert) => (
          <Tag color={getAlertColor(record.severity)}>
            {getAlertIcon(type)}
            <span style={{ marginLeft: 4 }}>{record.title}</span>
          </Tag>
        ),
      },
      {
        title: '严重程度',
        dataIndex: 'severity',
        key: 'severity',
        render: (severity: string) => (
          <Tag color={getAlertColor(severity)}>
            {severity === 'critical' ? '严重' :
             severity === 'high' ? '高' :
             severity === 'medium' ? '中' : '低'}
          </Tag>
        ),
      },
      {
        title: '分类',
        dataIndex: 'category',
        key: 'category',
        render: (category: string) => (
          <Tag>
            {category === 'market' ? '市场风险' :
             category === 'position' ? '持仓风险' :
             category === 'portfolio' ? '投资组合' : '系统风险'}
          </Tag>
        ),
      },
      {
        title: '时间',
        dataIndex: 'timestamp',
        key: 'timestamp',
        render: (timestamp: number) => new Date(timestamp).toLocaleString(),
      },
      {
        title: '状态',
        dataIndex: 'acknowledged',
        key: 'acknowledged',
        render: (acknowledged: boolean) => (
          <Tag color={acknowledged ? 'success' : 'warning'}>
            {acknowledged ? '已确认' : '待处理'}
          </Tag>
        ),
      },
      {
        title: '操作',
        key: 'action',
        render: (_, record: RiskAlert) => (
          <Button 
            type="link" 
            size="small" 
            onClick={() => handleAlertClick(record)}
          >
            {record.acknowledged ? '查看' : '处理'}
          </Button>
        ),
      },
    ];

    return (
      <Card title="风险警报" style={{ marginBottom: 16 }}>
        <Table
          dataSource={riskAlerts}
          columns={columns}
          rowKey="id"
          pagination={false}
          size="small"
        />
      </Card>
    );
  };

  // 渲染风险雷达图
  const renderRiskRadar = () => {
    if (!riskData.length || loading) return null;

    const validatedData = validateRiskData(riskData);
    
    const latestData = validatedData[validatedData.length - 1];
    const radarData = [
      { subject: '市场风险', A: (latestData.marketRisk || 0) * 100, fullMark: 100 },
      { subject: '信用风险', A: (latestData.creditRisk || 0) * 100, fullMark: 100 },
      { subject: '流动性风险', A: (latestData.liquidityRisk || 0) * 100, fullMark: 100 },
      { subject: '操作风险', A: (latestData.operationalRisk || 0) * 100, fullMark: 100 },
      { subject: 'VaR风险', A: (latestData.portfolioVaR || 0) * 100, fullMark: 100 },
      { subject: '压力测试', A: (latestData.stressTest || 0) * 100, fullMark: 100 },
    ];

    return (
      <Card title="风险雷达图">
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={radarData}>
            <PolarGrid />
            <PolarAngleAxis dataKey="subject" />
            <PolarRadiusAxis angle={90} domain={[0, 100]} />
            <Radar
              name="风险水平"
              dataKey="A"
              stroke="#1890ff"
              fill="#1890ff"
              fillOpacity={0.3}
            />
            <RechartsTooltip />
          </RadarChart>
        </ResponsiveContainer>
      </Card>
    );
  };

  return (
    <div style={{ padding: 24 }}>
      {/* 标题和控制 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={16}>
          <Title level={3}>风险分析 - {portfolioId}</Title>
          <Paragraph type="secondary">
            全面监控投资组合风险、市场风险和系统性风险
          </Paragraph>
        </Col>
        <Col span={8} style={{ textAlign: 'right' }}>
          <Space>
            <Select
              value={selectedTimeframe}
              onChange={handleTimeframeChange}
              style={{ width: 100 }}
            >
              <Option value="1h">1小时</Option>
              <Option value="4h">4小时</Option>
              <Option value="1d">1天</Option>
              <Option value="1w">1周</Option>
              <Option value="1M">1月</Option>
            </Select>
            
            <Button 
              icon={<SettingOutlined />} 
              size="small"
              onClick={() => setShowDetails(!showDetails)}
            >
              {showDetails ? '简化' : '详细'}
            </Button>
            
            <Button icon={<BellOutlined />} size="small">
              风险警报 ({riskAlerts.filter(a => !a.acknowledged).length})
            </Button>
          </Space>
        </Col>
      </Row>

      {/* 风险指标卡片 */}
      {renderRiskMetrics()}

      {/* 风险趋势图 */}
      <Card title="风险趋势分析" style={{ marginBottom: 16 }}>
        {renderRiskTrendChart()}
      </Card>

      {/* 持仓风险表格 */}
      {renderPositionRiskTable()}

      {/* 详细分析 */}
      {showDetails && (
        <>
          {renderRiskAlerts()}
          {renderRiskRadar()}
        </>
      )}

      {/* 风险报告 */}
      <Card title="风险报告" style={{ marginTop: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Alert
            message="风险总结"
            description={
              riskData.length > 0 ? 
              `当前投资组合风险水平为${getRiskLevel(riskData[riskData.length - 1].overallRisk)}，建议${riskData[riskData.length - 1].overallRisk > 0.6 ? '谨慎操作，适当减仓' : '维持当前策略，密切监控'}` :
              '正在加载风险数据...'
            }
            type={riskData.length > 0 && riskData[riskData.length - 1].overallRisk > 0.6 ? 'error' : 'info'}
            showIcon
          />
          
          <Alert
            message="风险建议"
            description={
              riskData.length > 0 && riskData[riskData.length - 1].portfolioVaR > 0.03 ? 
              'VaR超过阈值，建议调整投资组合或增加对冲策略。' :
              riskData.length > 0 && riskData[riskData.length - 1].marketRisk > 0.02 ?
              '市场风险较高，建议关注市场动态。' :
              '风险水平正常，建议继续保持当前策略。'
            }
            type={riskData.length > 0 && riskData[riskData.length - 1].portfolioVaR > 0.03 ? 'warning' : 'success'}
            showIcon
          />
          
          <Alert
            message="监控提醒"
            description="建议定期检查风险指标，及时处理风险警报，保持投资组合风险在可控范围内。"
            type="info"
            showIcon
          />
        </Space>
      </Card>

      {/* 警报详情模态框 */}
      <Modal
        title="风险警报详情"
        open={alertModalVisible}
        onCancel={() => setAlertModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setAlertModalVisible(false)}>
            关闭
          </Button>,
          <Button 
            key="acknowledge" 
            type="primary"
            onClick={() => selectedAlert && handleAlertAcknowledge(selectedAlert.id)}
            disabled={selectedAlert?.acknowledged}
          >
            确认警报
          </Button>,
        ]}
      >
        {selectedAlert && (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Alert
              message={selectedAlert.title}
              description={selectedAlert.description}
              type={selectedAlert.type}
              showIcon
            />
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="严重程度"
                  value={selectedAlert.severity}
                  valueStyle={{ color: getAlertColor(selectedAlert.severity) }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="警报时间"
                  value={new Date(selectedAlert.timestamp).toLocaleString()}
                />
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="分类"
                  value={selectedAlert.category}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="状态"
                  value={selectedAlert.acknowledged ? '已确认' : '待处理'}
                  valueStyle={{ color: selectedAlert.acknowledged ? '#52c41a' : '#faad14' }}
                />
              </Col>
            </Row>
          </Space>
        )}
      </Modal>
    </div>
  );
};

export default RiskAnalysis;