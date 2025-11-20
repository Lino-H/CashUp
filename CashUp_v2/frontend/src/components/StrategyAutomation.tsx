/**
 * 策略自动化组件
 * Strategy Automation Component
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
  InputNumber,
  Checkbox,
  TimePicker,
  DatePicker,
  notification,
  Popconfirm,
  Tree,
  Switch as SwitchAntd,
  
  Card as CardAntd,
  Timeline,
  Steps,
  Descriptions,
  Result,
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  SettingOutlined,
  BulbOutlined,
  ThunderboltOutlined,
  RobotOutlined,
  SafetyOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  InfoCircleOutlined,
  EyeOutlined,
  EditOutlined,
  PlusOutlined,
  DeleteOutlined,
  SyncOutlined,
  RocketOutlined,
  DollarOutlined,
  RiseOutlined,
  FallOutlined,
  StockOutlined,
  GlobalOutlined,
  BankOutlined,
  FundOutlined,
  ApiOutlined,
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  ExclamationCircleOutlined,
  CrownOutlined,
  HeartOutlined,
  ShareAltOutlined,
  ClockCircleOutlined,
  UserOutlined,
  TeamOutlined,
  FireOutlined,
  AntDesignOutlined,
  DollarOutlined as BanknoteOutlined,
  SafetyCertificateOutlined,
  DashboardOutlined,
  AlertOutlined,
  BellOutlined,
  TrophyOutlined,
  RobotOutlined as RobotOutlined2,
  ApiOutlined as ApiOutlined2,
  LineChartOutlined as LineChartOutlined2,
  PieChartOutlined as PieChartOutlined2,
  BarChartOutlined as BarChartOutlined2,
  ThunderboltOutlined as ThunderboltOutlined2,
  BulbOutlined as BulbOutlined2,
  SettingOutlined as SettingOutlined2,
  RobotOutlined as RobotOutlined3,
  ApiOutlined as ApiOutlined3,
  LineChartOutlined as LineChartOutlined3,
  PieChartOutlined as PieChartOutlined3,
  BarChartOutlined as BarChartOutlined3,
  ThunderboltOutlined as ThunderboltOutlined3,
  BulbOutlined as BulbOutlined3,
  SettingOutlined as SettingOutlined3,
  RobotOutlined as RobotOutlined4,
  ApiOutlined as ApiOutlined4,
  LineChartOutlined as LineChartOutlined4,
  PieChartOutlined as PieChartOutlined4,
  BarChartOutlined as BarChartOutlined4,
  ThunderboltOutlined as ThunderboltOutlined4,
  BulbOutlined as BulbOutlined4,
  SettingOutlined as SettingOutlined4,
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const RadioGroup = Radio.Group;
const { TabPane } = Tabs;
const { TextArea } = Input;
const { Step } = Steps;

// 策略自动化类型定义
export interface StrategyTemplate {
  id: string;
  name: string;
  description: string;
  category: 'trend' | 'momentum' | 'mean_reversion' | 'arbitrage' | 'scalping' | 'breakout' | 'hft' | 'ml';
  difficulty: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  parameters: {
    [key: string]: any;
  };
  performance: {
    winRate: number;
    avgReturn: number;
    maxDrawdown: number;
    sharpeRatio: number;
    totalTrades: number;
    profitFactor: number;
  };
  code: string;
  createdAt: number;
  updatedAt: number;
  author: string;
  tags: string[];
  rating: number;
  downloads: number;
}

export interface StrategyInstance {
  id: string;
  templateId: string;
  name: string;
  description: string;
  status: 'draft' | 'backtesting' | 'optimizing' | 'running' | 'paused' | 'stopped' | 'error';
  progress: number;
  parameters: {
    [key: string]: any;
  };
  backtestResults?: {
    totalReturn: number;
    winRate: number;
    maxDrawdown: number;
    sharpeRatio: number;
    profitFactor: number;
    trades: number;
  };
  optimizationResults?: {
    bestParameters: {
      [key: string]: any;
    };
    bestReturn: number;
    bestWinRate: number;
    bestSharpeRatio: number;
  };
  schedule?: {
    enabled: boolean;
    frequency: 'realtime' | '1m' | '5m' | '15m' | '1h' | '4h' | '1d' | '1w';
    startTime?: string;
    endTime?: string;
    daysOfWeek?: number[];
  };
  riskManagement?: {
    stopLoss: number;
    takeProfit: number;
    maxPosition: number;
    dailyLoss: number;
    maxDrawdown: number;
  };
  createdAt: number;
  lastRun: number;
  nextRun?: number;
  running: boolean;
}

export interface AutomationRule {
  id: string;
  name: string;
  type: 'schedule' | 'trigger' | 'condition' | 'alert';
  enabled: boolean;
  conditions: {
    [key: string]: any;
  };
  actions: {
    [key: string]: any;
  };
  priority: number;
  createdAt: number;
  lastExecuted: number;
  executionCount: number;
}

export interface BacktestJob {
  id: string;
  strategyInstanceId: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  startDate: string;
  endDate: string;
  timeframe: string;
  data: {
    totalTrades: number;
    winningTrades: number;
    losingTrades: number;
    totalReturn: number;
    annualizedReturn: number;
    maxDrawdown: number;
    sharpeRatio: number;
    profitFactor: number;
    avgTradeTime: number;
    winRate: number;
  };
  logs: string[];
  createdAt: number;
  completedAt?: number;
  estimatedDuration: number;
}

// 获取策略模板数据
const fetchStrategyTemplates = async (): Promise<StrategyTemplate[]> => {
  const response = await fetch('/api/strategies/templates');
  if (!response.ok) {
    throw new Error(`策略模板API错误: ${response.status} ${response.statusText}`);
  }
  return response.json();
};

// 获取策略实例数据
const fetchStrategyInstances = async (): Promise<StrategyInstance[]> => {
  const response = await fetch('/api/strategies/instances');
  if (!response.ok) {
    throw new Error(`策略实例API错误: ${response.status} ${response.statusText}`);
  }
  return response.json();
};

// 获取自动化规则数据
const fetchAutomationRules = async (): Promise<AutomationRule[]> => {
  const response = await fetch('/api/strategies/automation-rules');
  if (!response.ok) {
    throw new Error(`自动化规则API错误: ${response.status} ${response.statusText}`);
  }
  return response.json();
};

// 获取回测作业数据
const fetchBacktestJobs = async (): Promise<BacktestJob[]> => {
  const response = await fetch('/api/strategies/backtest-jobs');
  if (!response.ok) {
    throw new Error(`回测作业API错误: ${response.status} ${response.statusText}`);
  }
  return response.json();
};

// 状态颜色映射
const getStatusColor = (status: string): string => {
  switch (status) {
    case 'draft': return '#d9d9d9';
    case 'backtesting': return '#1890ff';
    case 'optimizing': return '#faad14';
    case 'running': return '#52c41a';
    case 'paused': return '#faad14';
    case 'stopped': return '#f5222d';
    case 'error': return '#ff4d4f';
    case 'pending': return '#1890ff';
    case 'completed': return '#52c41a';
    case 'failed': return '#f5222d';
    case 'cancelled': return '#faad14';
    default: return '#d9d9d9';
  }
};

// 状态描述映射
const getStatusDescription = (status: string): string => {
  switch (status) {
    case 'draft': return '草稿';
    case 'backtesting': return '回测中';
    case 'optimizing': return '优化中';
    case 'running': return '运行中';
    case 'paused': return '已暂停';
    case 'stopped': return '已停止';
    case 'error': return '错误';
    case 'pending': return '等待中';
    case 'completed': return '已完成';
    case 'failed': return '失败';
    case 'cancelled': return '已取消';
    default: return '未知';
  }
};

// 难度颜色映射
const getDifficultyColor = (difficulty: string): string => {
  switch (difficulty) {
    case 'beginner': return '#52c41a';
    case 'intermediate': return '#faad14';
    case 'advanced': return '#fa8c16';
    case 'expert': return '#f5222d';
    default: return '#d9d9d9';
  }
};

// 难度描述映射
const getDifficultyDescription = (difficulty: string): string => {
  switch (difficulty) {
    case 'beginner': return '初级';
    case 'intermediate': return '中级';
    case 'advanced': return '高级';
    case 'expert': return '专家';
    default: return '未知';
  }
};

interface StrategyAutomationProps {
  portfolioId?: string;
  autoRefresh?: boolean;
  onTemplateChange?: (templates: StrategyTemplate[]) => void;
  onInstanceChange?: (instances: StrategyInstance[]) => void;
}

const StrategyAutomation: React.FC<StrategyAutomationProps> = ({
  portfolioId = 'default',
  autoRefresh = true,
  onTemplateChange,
  onInstanceChange,
}) => {
  const [templates, setTemplates] = useState<StrategyTemplate[]>([]);
  const [instances, setInstances] = useState<StrategyInstance[]>([]);
  const [rules, setRules] = useState<AutomationRule[]>([]);
  const [jobs, setJobs] = useState<BacktestJob[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [selectedInstance, setSelectedInstance] = useState<string | null>(null);
  const [templateModalVisible, setTemplateModalVisible] = useState(false);
  const [instanceModalVisible, setInstanceModalVisible] = useState(false);
  const [ruleModalVisible, setRuleModalVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('templates');
  const [isSystemRunning, setIsSystemRunning] = useState(false);

  // 初始化数据
  useEffect(() => {
    const initializeData = async () => {
      setLoading(true);
      try {
        const [templatesData, instancesData, rulesData, jobsData] = await Promise.allSettled([
          fetchStrategyTemplates(),
          fetchStrategyInstances(),
          fetchAutomationRules(),
          fetchBacktestJobs()
        ]);
        
        if (templatesData.status === 'rejected') {
          message.error(`策略模板数据加载失败: ${templatesData.reason.message}`);
        } else {
          setTemplates(templatesData.value);
          onTemplateChange?.(templatesData.value);
        }
        
        if (instancesData.status === 'rejected') {
          message.error(`策略实例数据加载失败: ${instancesData.reason.message}`);
        } else {
          setInstances(instancesData.value);
          onInstanceChange?.(instancesData.value);
        }
        
        if (rulesData.status === 'rejected') {
          message.error(`自动化规则数据加载失败: ${rulesData.reason.message}`);
        } else {
          setRules(rulesData.value);
        }
        
        if (jobsData.status === 'rejected') {
          message.error(`回测作业数据加载失败: ${jobsData.reason.message}`);
        } else {
          setJobs(jobsData.value);
        }
      } catch (error) {
        console.error('Failed to initialize strategy automation data:', error);
        message.error('初始化数据失败');
      } finally {
        setLoading(false);
      }
    };

    initializeData();
  }, []);

  // 自动刷新
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(async () => {
      try {
        const [instancesData, jobsData] = await Promise.allSettled([
          fetchStrategyInstances(),
          fetchBacktestJobs()
        ]);
        
        if (instancesData.status === 'fulfilled') {
          setInstances(instancesData.value);
          onInstanceChange?.(instancesData.value);
        }
        
        if (jobsData.status === 'fulfilled') {
          setJobs(jobsData.value);
        }
      } catch (error) {
        console.error('Failed to refresh strategy automation data:', error);
      }
    }, 10000); // 每10秒刷新一次

    return () => clearInterval(interval);
  }, [autoRefresh, onInstanceChange]);

  // 处理策略实例状态切换
  const handleInstanceToggle = useCallback((instanceId: string) => {
    setInstances(prev => prev.map(instance => 
      instance.id === instanceId 
        ? { ...instance, running: !instance.running, status: !instance.running ? 'running' : 'paused' }
        : instance
    ));
    onInstanceChange?.(instances.map(instance => 
      instance.id === instanceId 
        ? { ...instance, running: !instance.running, status: !instance.running ? 'running' : 'paused' }
        : instance
    ));
    message.success('策略状态已更新');
  }, [instances, onInstanceChange]);

  // 处理系统运行状态切换
  const handleSystemToggle = useCallback(() => {
    setIsSystemRunning(!isSystemRunning);
    message.info(isSystemRunning ? '策略自动化系统已停止' : '策略自动化系统已启动');
  }, [isSystemRunning]);

  // 处理模板创建
  const handleCreateTemplate = useCallback((values: any) => {
    const newTemplate: StrategyTemplate = {
      id: `template_${Date.now()}`,
      name: values.name,
      description: values.description,
      category: values.category,
      difficulty: values.difficulty,
      parameters: values.parameters,
      performance: {
        winRate: 0,
        avgReturn: 0,
        maxDrawdown: 0,
        sharpeRatio: 0,
        totalTrades: 0,
        profitFactor: 0,
      },
      code: values.code,
      createdAt: Date.now(),
      updatedAt: Date.now(),
      author: '当前用户',
      tags: values.tags || [],
      rating: 0,
      downloads: 0,
    };
    
    setTemplates(prev => [...prev, newTemplate]);
    onTemplateChange?.([...templates, newTemplate]);
    setTemplateModalVisible(false);
    message.success('策略模板创建成功');
  }, [templates, onTemplateChange]);

  // 处理实例创建
  const handleCreateInstance = useCallback((values: any) => {
    const newInstance: StrategyInstance = {
      id: `instance_${Date.now()}`,
      templateId: values.templateId,
      name: values.name,
      description: values.description,
      status: 'draft',
      progress: 0,
      parameters: values.parameters,
      schedule: values.schedule,
      riskManagement: values.riskManagement,
      createdAt: Date.now(),
      lastRun: Date.now(),
      running: false,
    };
    
    setInstances(prev => [...prev, newInstance]);
    onInstanceChange?.([...instances, newInstance]);
    setInstanceModalVisible(false);
    message.success('策略实例创建成功');
  }, [instances, onInstanceChange]);

  // 处理规则创建
  const handleCreateRule = useCallback((values: any) => {
    const newRule: AutomationRule = {
      id: `rule_${Date.now()}`,
      name: values.name,
      type: values.type,
      enabled: values.enabled,
      conditions: values.conditions,
      actions: values.actions,
      priority: values.priority,
      createdAt: Date.now(),
      lastExecuted: Date.now(),
      executionCount: 0,
    };
    
    setRules(prev => [...prev, newRule]);
    message.success('自动化规则创建成功');
  }, []);

  // 处理回测作业启动
  const handleStartBacktest = useCallback((jobId: string) => {
    setJobs(prev => prev.map(job => 
      job.id === jobId 
        ? { ...job, status: 'running', progress: 0 }
        : job
    ));
    message.success('回测作业已启动');
  }, []);

  // 模板表格列
  const templateColumns = [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: StrategyTemplate) => (
        <Space>
          <Avatar size="small" icon={<ThunderboltOutlined />} />
          <Text strong>{text}</Text>
        </Space>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => {
        const categoryMap = {
          trend: '趋势跟踪',
          momentum: '动量',
          mean_reversion: '均值回归',
          arbitrage: '套利',
          scalping: '高频',
          breakout: '突破',
          hft: '超高频',
          ml: '机器学习',
        };
        return <Tag>{categoryMap[category as keyof typeof categoryMap]}</Tag>;
      },
    },
    {
      title: '难度',
      dataIndex: 'difficulty',
      key: 'difficulty',
      render: (difficulty: string) => (
        <Tag color={getDifficultyColor(difficulty)}>
          {getDifficultyDescription(difficulty)}
        </Tag>
      ),
    },
    {
      title: '评分',
      dataIndex: 'rating',
      key: 'rating',
      render: (rating: number) => (
        <Rate disabled defaultValue={rating} />
      ),
    },
    {
      title: '下载量',
      dataIndex: 'downloads',
      key: 'downloads',
      render: (downloads: number) => (
        <Text>{downloads}</Text>
      ),
    },
    {
      title: '胜率',
      dataIndex: 'performance',
      key: 'winRate',
      render: (performance: StrategyTemplate['performance']) => (
        <span style={{ color: performance.winRate >= 0.5 ? '#52c41a' : '#faad14' }}>
          {(performance.winRate * 100).toFixed(1)}%
        </span>
      ),
    },
    {
      title: '夏普比率',
      dataIndex: 'performance',
      key: 'sharpeRatio',
      render: (performance: StrategyTemplate['performance']) => (
        <span style={{ color: performance.sharpeRatio >= 1 ? '#52c41a' : '#faad14' }}>
          {performance.sharpeRatio.toFixed(2)}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: StrategyTemplate) => (
        <Space>
          <Button 
            type="link" 
            size="small" 
            onClick={() => setSelectedTemplate(record.id)}
          >
            详情
          </Button>
          <Button 
            type="link" 
            size="small" 
            onClick={() => {
              setSelectedTemplate(record.id);
              setInstanceModalVisible(true);
            }}
          >
            创建实例
          </Button>
        </Space>
      ),
    },
  ];

  // 实例表格列
  const instanceColumns = [
    {
      title: '实例名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: StrategyInstance) => (
        <Space>
          {record.running ? <PlayCircleOutlined style={{ color: '#52c41a' }} /> : <PauseCircleOutlined style={{ color: '#faad14' }} />}
          <Text strong>{text}</Text>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {getStatusDescription(status)}
        </Tag>
      ),
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      render: (progress: number) => (
        <Progress percent={progress} size="small" />
      ),
    },
    {
      title: '下次运行',
      dataIndex: 'nextRun',
      key: 'nextRun',
      render: (nextRun?: number) => nextRun ? new Date(nextRun).toLocaleString() : '无',
    },
    {
      title: '总收益',
      dataIndex: 'backtestResults',
      key: 'totalReturn',
      render: (results?: StrategyInstance['backtestResults']) => results ? (
        <span style={{ color: results.totalReturn >= 0 ? '#52c41a' : '#f5222d' }}>
          {results.totalReturn >= 0 ? '+' : ''}{(results.totalReturn * 100).toFixed(2)}%
        </span>
      ) : '-',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: StrategyInstance) => (
        <Space>
          <Button 
            type="link" 
            size="small" 
            onClick={() => handleInstanceToggle(record.id)}
            icon={record.running ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
          >
            {record.running ? '暂停' : '启动'}
          </Button>
          <Button 
            type="link" 
            size="small" 
            onClick={() => setSelectedInstance(record.id)}
          >
            详情
          </Button>
          <Button 
            type="link" 
            size="small" 
            icon={<ThunderboltOutlined />}
            onClick={() => handleStartBacktest(record.id)}
          >
            回测
          </Button>
        </Space>
      ),
    },
  ];

  // 规则表格列
  const ruleColumns = [
    {
      title: '规则名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: AutomationRule) => (
        <Space>
          <Switch
            checked={record.enabled}
            onChange={(checked) => {
              setRules(prev => prev.map(r => 
                r.id === record.id ? { ...r, enabled: checked } : r
              ));
            }}
          />
          <Text strong>{text}</Text>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const typeMap = {
          schedule: '定时',
          trigger: '触发',
          condition: '条件',
          alert: '警报',
        };
        return <Tag>{typeMap[type as keyof typeof typeMap]}</Tag>;
      },
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority: number) => (
        <Badge count={priority} showZero />
      ),
    },
    {
      title: '执行次数',
      dataIndex: 'executionCount',
      key: 'executionCount',
      render: (count: number) => (
        <Text>{count}</Text>
      ),
    },
    {
      title: '最后执行',
      dataIndex: 'lastExecuted',
      key: 'lastExecuted',
      render: (timestamp: number) => new Date(timestamp).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: AutomationRule) => (
        <Space>
          <Button 
            type="link" 
            size="small" 
            onClick={() => setRuleModalVisible(true)}
          >
            编辑
          </Button>
        </Space>
      ),
    },
  ];

  // 作业表格列
  const jobColumns = [
    {
      title: '策略实例',
      dataIndex: 'strategyInstanceId',
      key: 'strategyInstanceId',
      render: (instanceId: string) => instances.find(i => i.id === instanceId)?.name || instanceId,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {getStatusDescription(status)}
        </Tag>
      ),
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      render: (progress: number) => (
        <Progress percent={progress} size="small" />
      ),
    },
    {
      title: '时间范围',
      dataIndex: 'startDate',
      key: 'dateRange',
      render: (_: any, record: BacktestJob) => (
        <Text>{record.startDate} - {record.endDate}</Text>
      ),
    },
    {
      title: '总收益',
      dataIndex: 'data',
      key: 'totalReturn',
      render: (data: BacktestJob['data']) => (
        <span style={{ color: data.totalReturn >= 0 ? '#52c41a' : '#f5222d' }}>
          {data.totalReturn >= 0 ? '+' : ''}{(data.totalReturn * 100).toFixed(2)}%
        </span>
      ),
    },
    {
      title: '胜率',
      dataIndex: 'data',
      key: 'winRate',
      render: (data: BacktestJob['data']) => (
        <span style={{ color: data.winRate >= 0.5 ? '#52c41a' : '#faad14' }}>
          {(data.winRate * 100).toFixed(1)}%
        </span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: BacktestJob) => (
        <Space>
          {record.status === 'pending' && (
            <Button 
              type="link" 
              size="small" 
              onClick={() => handleStartBacktest(record.id)}
            >
              启动
            </Button>
          )}
          <Button 
            type="link" 
            size="small" 
            onClick={() => setSelectedInstance(record.strategyInstanceId)}
          >
            查看详情
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      {/* 标题和控制 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={16}>
          <Title level={3}>策略自动化 - {portfolioId}</Title>
          <Paragraph type="secondary">
            智能化策略管理，支持模板创建、实例管理、自动化规则和回测分析
          </Paragraph>
        </Col>
        <Col span={8} style={{ textAlign: 'right' }}>
          <Space>
            <Switch
              checkedChildren="运行中"
              unCheckedChildren="已停止"
              checked={isSystemRunning}
              onChange={handleSystemToggle}
              loading={loading}
            />
            <Button 
              type={isSystemRunning ? 'default' : 'primary'}
              icon={isSystemRunning ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
              onClick={handleSystemToggle}
              loading={loading}
            >
              {isSystemRunning ? '停止系统' : '启动系统'}
            </Button>
            <Button icon={<SettingOutlined />} onClick={() => setRuleModalVisible(true)}>
              规则设置
            </Button>
          </Space>
        </Col>
      </Row>

      {/* 系统状态概览 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="策略模板"
              value={templates.length}
              valueStyle={{ color: '#1890ff' }}
              prefix={<ThunderboltOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="策略实例"
              value={instances.filter(i => i.running).length}
              suffix={`/ ${instances.length}`}
              valueStyle={{ color: '#52c41a' }}
              prefix={<RobotOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="自动化规则"
              value={rules.filter(r => r.enabled).length}
              suffix={`/ ${rules.length}`}
              valueStyle={{ color: '#faad14' }}
              prefix={<ApiOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="回测作业"
              value={jobs.filter(j => j.status === 'running').length}
              valueStyle={{ color: '#722ed1' }}
              prefix={<LineChartOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 标签页 */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="策略模板" key="templates">
            <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
              <Col span={24}>
                <Space>
                  <Button 
                    type="primary" 
                    icon={<PlusOutlined />}
                    onClick={() => setTemplateModalVisible(true)}
                  >
                    创建模板
                  </Button>
                  <Button icon={<SyncOutlined />} onClick={() => window.location.reload()}>
                    刷新
                  </Button>
                </Space>
              </Col>
            </Row>
            
            <Table
              dataSource={templates}
              columns={templateColumns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              loading={loading}
              size="small"
            />
          </TabPane>
          
          <TabPane tab="策略实例" key="instances">
            <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
              <Col span={24}>
                <Space>
                  <Button 
                    type="primary" 
                    icon={<PlusOutlined />}
                    onClick={() => setInstanceModalVisible(true)}
                  >
                    创建实例
                  </Button>
                  <Button icon={<SyncOutlined />} onClick={() => window.location.reload()}>
                    刷新
                  </Button>
                </Space>
              </Col>
            </Row>
            
            <Table
              dataSource={instances}
              columns={instanceColumns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              loading={loading}
              size="small"
            />
          </TabPane>
          
          <TabPane tab="自动化规则" key="rules">
            <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
              <Col span={24}>
                <Space>
                  <Button 
                    type="primary" 
                    icon={<PlusOutlined />}
                    onClick={() => setRuleModalVisible(true)}
                  >
                    创建规则
                  </Button>
                  <Button icon={<SyncOutlined />} onClick={() => window.location.reload()}>
                    刷新
                  </Button>
                </Space>
              </Col>
            </Row>
            
            <Table
              dataSource={rules}
              columns={ruleColumns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              loading={loading}
              size="small"
            />
          </TabPane>
          
          <TabPane tab="回测作业" key="jobs">
            <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
              <Col span={24}>
                <Space>
                  <Button icon={<SyncOutlined />} onClick={() => window.location.reload()}>
                    刷新
                  </Button>
                </Space>
              </Col>
            </Row>
            
            <Table
              dataSource={jobs}
              columns={jobColumns}
              rowKey="id"
              pagination={{ pageSize: 20 }}
              loading={loading}
              size="small"
            />
          </TabPane>
        </Tabs>
      </Card>

      {/* 创建策略模板模态框 */}
      <Modal
        title="创建策略模板"
        open={templateModalVisible}
        onCancel={() => setTemplateModalVisible(false)}
        footer={null}
        width={1000}
      >
        <Form
          layout="vertical"
          onFinish={handleCreateTemplate}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="策略名称"
                name="name"
                rules={[{ required: true, message: '请输入策略名称' }]}
              >
                <Input placeholder="输入策略名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="策略分类"
                name="category"
                rules={[{ required: true, message: '请选择策略分类' }]}
              >
                <Select>
                  <Option value="trend">趋势跟踪</Option>
                  <Option value="momentum">动量</Option>
                  <Option value="mean_reversion">均值回归</Option>
                  <Option value="arbitrage">套利</Option>
                  <Option value="scalping">高频</Option>
                  <Option value="breakout">突破</Option>
                  <Option value="hft">超高频</Option>
                  <Option value="ml">机器学习</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item
            label="策略描述"
            name="description"
            rules={[{ required: true, message: '请输入策略描述' }]}
          >
            <TextArea rows={3} placeholder="输入策略描述" />
          </Form.Item>
          
          <Form.Item
            label="策略难度"
            name="difficulty"
            rules={[{ required: true, message: '请选择策略难度' }]}
          >
            <Select>
              <Option value="beginner">初级</Option>
              <Option value="intermediate">中级</Option>
              <Option value="advanced">高级</Option>
              <Option value="expert">专家</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            label="策略参数"
            name="parameters"
            rules={[{ required: true, message: '请输入策略参数' }]}
          >
            <TextArea rows={4} placeholder="输入JSON格式的策略参数" />
          </Form.Item>
          
          <Form.Item
            label="策略代码"
            name="code"
            rules={[{ required: true, message: '请输入策略代码' }]}
          >
            <TextArea rows={6} placeholder="输入策略代码" />
          </Form.Item>
          
          <Form.Item
            label="标签"
            name="tags"
          >
            <Select mode="tags" placeholder="输入标签" />
          </Form.Item>
          
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                创建模板
              </Button>
              <Button onClick={() => setTemplateModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 创建策略实例模态框 */}
      <Modal
        title="创建策略实例"
        open={instanceModalVisible}
        onCancel={() => setInstanceModalVisible(false)}
        footer={null}
        width={1000}
      >
        <Form
          layout="vertical"
          onFinish={handleCreateInstance}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="选择模板"
                name="templateId"
                rules={[{ required: true, message: '请选择策略模板' }]}
              >
                <Select>
                  {templates.map(template => (
                    <Option key={template.id} value={template.id}>
                      {template.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="实例名称"
                name="name"
                rules={[{ required: true, message: '请输入实例名称' }]}
              >
                <Input placeholder="输入实例名称" />
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item
            label="实例描述"
            name="description"
            rules={[{ required: true, message: '请输入实例描述' }]}
          >
            <TextArea rows={3} placeholder="输入实例描述" />
          </Form.Item>
          
          <Form.Item
            label="策略参数"
            name="parameters"
            rules={[{ required: true, message: '请输入策略参数' }]}
          >
            <TextArea rows={4} placeholder="输入JSON格式的策略参数" />
          </Form.Item>
          
          <Form.Item
            label="执行计划"
            name="schedule"
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <Form.Item name="schedule.enabled" valuePropName="checked">
                <Switch checkedChildren="启用" unCheckedChildren="禁用" />
              </Form.Item>
              <Form.Item name="schedule.frequency">
                <Select>
                  <Option value="realtime">实时</Option>
                  <Option value="1m">1分钟</Option>
                  <Option value="5m">5分钟</Option>
                  <Option value="15m">15分钟</Option>
                  <Option value="1h">1小时</Option>
                  <Option value="4h">4小时</Option>
                  <Option value="1d">1天</Option>
                  <Option value="1w">1周</Option>
                </Select>
              </Form.Item>
            </Space>
          </Form.Item>
          
          <Form.Item
            label="风险管理"
            name="riskManagement"
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <Row gutter={16}>
                <Col span={6}>
                  <Form.Item name="riskManagement.stopLoss">
                    <InputNumber placeholder="止损" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item name="riskManagement.takeProfit">
                    <InputNumber placeholder="止盈" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item name="riskManagement.maxPosition">
                    <InputNumber placeholder="最大持仓" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item name="riskManagement.dailyLoss">
                    <InputNumber placeholder="日亏损" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
            </Space>
          </Form.Item>
          
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                创建实例
              </Button>
              <Button onClick={() => setInstanceModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 策略模板详情模态框 */}
      <Modal
        title="策略模板详情"
        open={!!selectedTemplate}
        onCancel={() => setSelectedTemplate(null)}
        footer={null}
        width={1000}
      >
        {selectedTemplate && templates.find(t => t.id === selectedTemplate) && (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Row gutter={16}>
              <Col span={12}>
                <Text strong>策略名称：</Text>
                <Text>{templates.find(t => t.id === selectedTemplate)?.name}</Text>
              </Col>
              <Col span={12}>
                <Text strong>策略分类：</Text>
                <Text>{templates.find(t => t.id === selectedTemplate)?.category}</Text>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={12}>
                <Text strong>难度等级：</Text>
                <Text>{templates.find(t => t.id === selectedTemplate)?.difficulty}</Text>
              </Col>
              <Col span={12}>
                <Text strong>作者：</Text>
                <Text>{templates.find(t => t.id === selectedTemplate)?.author}</Text>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={12}>
                <Text strong>创建时间：</Text>
                <Text>{new Date(templates.find(t => t.id === selectedTemplate)?.createdAt || 0).toLocaleString()}</Text>
              </Col>
              <Col span={12}>
                <Text strong>最后更新：</Text>
                <Text>{new Date(templates.find(t => t.id === selectedTemplate)?.updatedAt || 0).toLocaleString()}</Text>
              </Col>
            </Row>
            <Divider />
            <Text strong>策略描述：</Text>
            <Paragraph>{templates.find(t => t.id === selectedTemplate)?.description}</Paragraph>
            
            <Divider />
            <Text strong>策略参数：</Text>
            <Paragraph>{JSON.stringify(templates.find(t => t.id === selectedTemplate)?.parameters, null, 2)}</Paragraph>
            
            <Divider />
            <Text strong>策略代码：</Text>
            <Card size="small">
              <pre style={{ background: '#f5f5f5', padding: 16, borderRadius: 4 }}>
                {templates.find(t => t.id === selectedTemplate)?.code}
              </pre>
            </Card>
            
            <Divider />
            <Text strong>性能指标：</Text>
            <Row gutter={16}>
              <Col span={8}>
                <Statistic title="胜率" value={(templates.find(t => t.id === selectedTemplate)?.performance.winRate || 0 * 100).toFixed(1)} suffix="%" />
              </Col>
              <Col span={8}>
                <Statistic title="夏普比率" value={templates.find(t => t.id === selectedTemplate)?.performance.sharpeRatio.toFixed(2)} />
              </Col>
              <Col span={8}>
                <Statistic title="总交易次数" value={templates.find(t => t.id === selectedTemplate)?.performance.totalTrades} />
              </Col>
            </Row>
          </Space>
        )}
      </Modal>

      {/* 策略实例详情模态框 */}
      <Modal
        title="策略实例详情"
        open={!!selectedInstance}
        onCancel={() => setSelectedInstance(null)}
        footer={null}
        width={1000}
      >
        {selectedInstance && instances.find(i => i.id === selectedInstance) && (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Row gutter={16}>
              <Col span={12}>
                <Text strong>实例名称：</Text>
                <Text>{instances.find(i => i.id === selectedInstance)?.name}</Text>
              </Col>
              <Col span={12}>
                <Text strong>状态：</Text>
                <Tag color={getStatusColor(instances.find(i => i.id === selectedInstance)?.status || '')}>
                  {getStatusDescription(instances.find(i => i.id === selectedInstance)?.status || '')}
                </Tag>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={12}>
                <Text strong>创建时间：</Text>
                <Text>{new Date(instances.find(i => i.id === selectedInstance)?.createdAt || 0).toLocaleString()}</Text>
              </Col>
              <Col span={12}>
                <Text strong>最后运行：</Text>
                <Text>{new Date(instances.find(i => i.id === selectedInstance)?.lastRun || 0).toLocaleString()}</Text>
              </Col>
            </Row>
            
            <Divider />
            <Text strong>实例描述：</Text>
            <Paragraph>{instances.find(i => i.id === selectedInstance)?.description}</Paragraph>
            
            <Divider />
            <Text strong>策略参数：</Text>
            <Paragraph>{JSON.stringify(instances.find(i => i.id === selectedInstance)?.parameters, null, 2)}</Paragraph>
            
            {instances.find(i => i.id === selectedInstance)?.backtestResults && (
              <>
                <Divider />
                <Text strong>回测结果：</Text>
                <Row gutter={16}>
                  <Col span={6}>
                    <Statistic title="总收益" value={(instances.find(i => i.id === selectedInstance)?.backtestResults?.totalReturn || 0 * 100).toFixed(2)} suffix="%" />
                  </Col>
                  <Col span={6}>
                    <Statistic title="胜率" value={(instances.find(i => i.id === selectedInstance)?.backtestResults?.winRate || 0 * 100).toFixed(1)} suffix="%" />
                  </Col>
                  <Col span={6}>
                    <Statistic title="最大回撤" value={(instances.find(i => i.id === selectedInstance)?.backtestResults?.maxDrawdown || 0 * 100).toFixed(2)} suffix="%" />
                  </Col>
                  <Col span={6}>
                    <Statistic title="夏普比率" value={instances.find(i => i.id === selectedInstance)?.backtestResults?.sharpeRatio.toFixed(2)} />
                  </Col>
                </Row>
              </>
            )}
            
            {instances.find(i => i.id === selectedInstance)?.schedule && (
              <>
                <Divider />
                <Text strong>执行计划：</Text>
                <Row gutter={16}>
                  <Col span={6}>
                    <Text>启用状态：</Text>
                    <Tag color={instances.find(i => i.id === selectedInstance)?.schedule?.enabled ? '#52c41a' : '#f5222d'}>
                      {instances.find(i => i.id === selectedInstance)?.schedule?.enabled ? '启用' : '禁用'}
                    </Tag>
                  </Col>
                  <Col span={6}>
                    <Text>执行频率：</Text>
                    <Text>{instances.find(i => i.id === selectedInstance)?.schedule?.frequency}</Text>
                  </Col>
                  <Col span={6}>
                    <Text>开始时间：</Text>
                    <Text>{instances.find(i => i.id === selectedInstance)?.schedule?.startTime}</Text>
                  </Col>
                  <Col span={6}>
                    <Text>结束时间：</Text>
                    <Text>{instances.find(i => i.id === selectedInstance)?.schedule?.endTime}</Text>
                  </Col>
                </Row>
              </>
            )}
          </Space>
        )}
      </Modal>
    </div>
  );
};

export default StrategyAutomation;
