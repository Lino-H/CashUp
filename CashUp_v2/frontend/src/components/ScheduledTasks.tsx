/**
 * 定时任务组件
 * Scheduled Tasks Component
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
  InputGroup,
  Card as CardAntd,
  Timeline,
  Steps,
  Descriptions,
  Result,
  Cascader,
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
  TrendingUpOutlined,
  TrendingDownOutlined,
  StockOutlined,
  GlobalOutlined,
  BankOutlined,
  FundOutlined,
  ApiOutlined,
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  ExclamationTriangleOutlined,
  CrownOutlined,
  HeartOutlined,
  ShareAltOutlined,
  ClockCircleOutlined,
  UserOutlined,
  TeamOutlined,
  FireOutlined,
  RocketLaunchOutlined,
  AntDesignOutlined,
  BanknoteOutlined,
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
  ClockCircleOutlined as ClockCircleOutlined2,
  UserOutlined as UserOutlined2,
  TeamOutlined as TeamOutlined2,
  FireOutlined as FireOutlined2,
  RocketLaunchOutlined as RocketLaunchOutlined2,
  AntDesignOutlined as AntDesignOutlined2,
  BanknoteOutlined as BanknoteOutlined2,
  SafetyCertificateOutlined as SafetyCertificateOutlined2,
  DashboardOutlined as DashboardOutlined2,
  AlertOutlined as AlertOutlined2,
  BellOutlined as BellOutlined2,
  TrophyOutlined as TrophyOutlined2,
  PlusOutlined as PlusOutlined2,
  EditOutlined as EditOutlined2,
  DeleteOutlined as DeleteOutlined2,
  SyncOutlined as SyncOutlined2,
  CheckCircleOutlined as CheckCircleOutlined2,
  CloseCircleOutlined as CloseCircleOutlined2,
  InfoCircleOutlined as InfoCircleOutlined2,
  PlayCircleOutlined as PlayCircleOutlined2,
  PauseCircleOutlined as PauseCircleOutlined2,
  StopOutlined as StopOutlined2,
  SettingOutlined as SettingOutlined4,
  BulbOutlined as BulbOutlined4,
  ThunderboltOutlined as ThunderboltOutlined4,
  RobotOutlined as RobotOutlined4,
  SafetyOutlined as SafetyOutlined2,
  WarningOutlined as WarningOutlined2,
  BellOutlined as BellOutlined2,
  ApiOutlined as ApiOutlined2,
  LineChartOutlined as LineChartOutlined2,
  PieChartOutlined as PieChartOutlined2,
  BarChartOutlined as BarChartOutlined2,
  DashboardOutlined as DashboardOutlined2,
  AlertOutlined as AlertOutlined2,
  ClockCircleOutlined as ClockCircleOutlined2,
  UserOutlined as UserOutlined2,
  TeamOutlined as TeamOutlined2,
  FireOutlined as FireOutlined2,
  RocketLaunchOutlined as RocketLaunchOutlined2,
  AntDesignOutlined as AntDesignOutlined2,
  BanknoteOutlined as BanknoteOutlined2,
  SafetyCertificateOutlined as SafetyCertificateOutlined2,
  MessageOutlined,
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { RadioGroup } = Radio;
const { TabPane } = Tabs;
const { TextArea } = Input;
const { Step } = Steps;

// 定时任务类型定义
export interface ScheduledTask {
  id: string;
  name: string;
  description: string;
  type: 'data_sync' | 'strategy_run' | 'report_generation' | 'system_maintenance' | 'backup' | 'alert' | 'notification' | 'cleanup';
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'paused';
  schedule: {
    type: 'cron' | 'interval' | 'once' | 'calendar';
    expression: string;
    timezone: string;
    enabled: boolean;
    startDate?: string;
    endDate?: string;
    runAt?: string;
    interval?: number;
    repeatCount?: number;
  };
  triggerConditions?: {
    [key: string]: any;
  };
  actions: {
    [key: string]: any;
  };
  priority: 'low' | 'medium' | 'high' | 'critical';
  retryPolicy: {
    maxRetries: number;
    retryInterval: number;
    backoffMultiplier: number;
  };
  timeout: number;
  maxExecutionTime: number;
  dependencies: string[];
  executionHistory: ExecutionRecord[];
  createdAt: number;
  lastRun?: number;
  nextRun?: number;
  enabled: boolean;
  running: boolean;
}

export interface ExecutionRecord {
  id: string;
  taskId: string;
  startTime: number;
  endTime?: number;
  status: 'success' | 'failed' | 'timeout' | 'cancelled';
  result?: any;
  error?: string;
  duration?: number;
  logs: string[];
}

export interface TaskTemplate {
  id: string;
  name: string;
  description: string;
  type: 'data_sync' | 'strategy_run' | 'report_generation' | 'system_maintenance' | 'backup' | 'alert' | 'notification' | 'cleanup';
  category: 'data' | 'trading' | 'reporting' | 'system' | 'backup' | 'alert';
  scheduleDefaults: {
    type: 'cron' | 'interval' | 'once' | 'calendar';
    expression: string;
    timezone: string;
    interval?: number;
  };
  actionDefaults: {
    [key: string]: any;
  };
  icon: React.ReactNode;
  color: string;
  difficulty: 'easy' | 'medium' | 'hard';
  tags: string[];
}

export interface TaskGroup {
  id: string;
  name: string;
  description: string;
  tasks: string[];
  priority: 'low' | 'medium' | 'high';
  enabled: boolean;
  createdAt: number;
}

// 生成模拟定时任务数据
const generateMockScheduledTasks = (): ScheduledTask[] => {
  const tasks: ScheduledTask[] = [];
  const types = ['data_sync', 'strategy_run', 'report_generation', 'system_maintenance', 'backup', 'alert', 'notification', 'cleanup'] as const;
  const statuses = ['pending', 'running', 'completed', 'failed', 'cancelled', 'paused'] as const;
  const priorities = ['low', 'medium', 'high', 'critical'] as const;
  
  for (let i = 0; i < 15; i++) {
    tasks.push({
      id: `task_${i}`,
      name: `任务_${i + 1}`,
      description: `这是第${i + 1}个定时任务的描述`,
      type: types[i % types.length],
      status: statuses[Math.floor(Math.random() * statuses.length)],
      schedule: {
        type: ['cron', 'interval', 'once', 'calendar'][Math.floor(Math.random() * 4)] as 'cron' | 'interval' | 'once' | 'calendar',
        expression: i % 4 === 0 ? '0 0 9 * * *' : i % 4 === 1 ? '*/5 * * * *' : i % 4 === 2 ? '0 0 * * *' : '0 0 1 1 *',
        timezone: 'Asia/Shanghai',
        enabled: Math.random() > 0.2,
        startDate: '2024-01-01',
        endDate: '2024-12-31',
        interval: 300,
        repeatCount: 10,
      },
      triggerConditions: {
        marketOpen: true,
        volumeThreshold: 1000,
        priceChange: 0.05,
      },
      actions: {
        action: 'notify',
        message: '任务执行完成',
        recipients: ['admin@example.com'],
      },
      priority: priorities[Math.floor(Math.random() * priorities.length)],
      retryPolicy: {
        maxRetries: 3,
        retryInterval: 60,
        backoffMultiplier: 2,
      },
      timeout: 300,
      maxExecutionTime: 600,
      dependencies: [],
      executionHistory: [],
      createdAt: Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000,
      lastRun: Math.random() > 0.5 ? Date.now() - Math.random() * 24 * 60 * 60 * 1000 : undefined,
      nextRun: Date.now() + Math.random() * 24 * 60 * 60 * 1000,
      enabled: Math.random() > 0.2,
      running: Math.random() > 0.7,
    });
  }
  
  return tasks;
};

// 生成模拟执行记录数据
const generateMockExecutionHistory = (taskId: string): ExecutionRecord[] => {
  const records: ExecutionRecord[] = [];
  const statuses = ['success', 'failed', 'timeout', 'cancelled'] as const;
  
  for (let i = 0; i < 10; i++) {
    records.push({
      id: `record_${i}`,
      taskId,
      startTime: Date.now() - (i + 1) * 60 * 60 * 1000,
      endTime: Date.now() - i * 60 * 60 * 1000,
      status: statuses[Math.floor(Math.random() * statuses.length)],
      result: { success: true, message: '任务执行成功' },
      duration: Math.random() * 300 + 60,
      logs: [
        '开始执行任务...',
        '加载数据...',
        '执行逻辑...',
        '完成执行...',
      ],
    });
  }
  
  return records.sort((a, b) => b.startTime - a.startTime);
};

// 生成模拟任务模板数据
const generateMockTaskTemplates = (): TaskTemplate[] => {
  return [
    {
      id: 'template_data_sync',
      name: '数据同步',
      description: '定时同步市场数据和交易数据',
      type: 'data_sync',
      category: 'data',
      scheduleDefaults: {
        type: 'cron',
        expression: '*/5 * * * *',
        timezone: 'Asia/Shanghai',
      },
      actionDefaults: {
        source: 'exchange',
        target: 'database',
        dataType: 'market',
      },
      icon: <SyncOutlined />,
      color: '#1890ff',
      difficulty: 'easy',
      tags: ['数据', '同步', '实时'],
    },
    {
      id: 'template_strategy_run',
      name: '策略执行',
      description: '定时运行交易策略',
      type: 'strategy_run',
      category: 'trading',
      scheduleDefaults: {
        type: 'cron',
        expression: '0 */1 * * * *',
        timezone: 'Asia/Shanghai',
      },
      actionDefaults: {
        strategy: 'default',
        symbol: 'BTC/USDT',
        action: 'trade',
      },
      icon: <RobotOutlined />,
      color: '#52c41a',
      difficulty: 'medium',
      tags: ['策略', '交易', '自动化'],
    },
    {
      id: 'template_report_generation',
      name: '报告生成',
      description: '定时生成交易报告和分析报告',
      type: 'report_generation',
      category: 'reporting',
      scheduleDefaults: {
        type: 'cron',
        expression: '0 0 9 * * *',
        timezone: 'Asia/Shanghai',
      },
      actionDefaults: {
        reportType: 'daily',
        format: 'pdf',
        recipients: ['admin@example.com'],
      },
      icon: <LineChartOutlined />,
      color: '#722ed1',
      difficulty: 'medium',
      tags: ['报告', '分析', '日报'],
    },
    {
      id: 'template_system_maintenance',
      name: '系统维护',
      description: '定时系统维护和清理',
      type: 'system_maintenance',
      category: 'system',
      scheduleDefaults: {
        type: 'cron',
        expression: '0 2 * * 0',
        timezone: 'Asia/Shanghai',
      },
      actionDefaults: {
        maintenanceType: 'cleanup',
        retentionDays: 30,
      },
      icon: <SafetyCertificateOutlined />,
      color: '#fa8c16',
      difficulty: 'easy',
      tags: ['维护', '清理', '系统'],
    },
    {
      id: 'template_backup',
      name: '数据备份',
      description: '定时备份数据库和重要文件',
      type: 'backup',
      category: 'backup',
      scheduleDefaults: {
        type: 'cron',
        expression: '0 3 * * *',
        timezone: 'Asia/Shanghai',
      },
      actionDefaults: {
        backupType: 'full',
        location: '/backup',
        retentionDays: 7,
      },
      icon: <BanknoteOutlined />,
      color: '#eb2f96',
      difficulty: 'medium',
      tags: ['备份', '数据', '安全'],
    },
    {
      id: 'template_alert',
      name: '警报通知',
      description: '定时检查系统状态并发送警报',
      type: 'alert',
      category: 'alert',
      scheduleDefaults: {
        type: 'cron',
        expression: '*/10 * * * *',
        timezone: 'Asia/Shanghai',
      },
      actionDefaults: {
        alertType: 'health_check',
        channels: ['email', 'sms'],
        severity: 'warning',
      },
      icon: <BellOutlined />,
      color: '#f5222d',
      difficulty: 'easy',
      tags: ['警报', '通知', '监控'],
    },
    {
      id: 'template_notification',
      name: '通知发送',
      description: '定时发送系统通知和用户通知',
      type: 'notification',
      category: 'alert',
      scheduleDefaults: {
        type: 'cron',
        expression: '0 */30 * * * *',
        timezone: 'Asia/Shanghai',
      },
      actionDefaults: {
        notificationType: 'system',
        channels: ['email', 'push'],
        template: 'default',
      },
      icon: <MessageOutlined />,
      color: '#13c2c2',
      difficulty: 'easy',
      tags: ['通知', '消息', '推送'],
    },
    {
      id: 'template_cleanup',
      name: '清理任务',
      description: '定时清理临时文件和过期数据',
      type: 'cleanup',
      category: 'system',
      scheduleDefaults: {
        type: 'cron',
        expression: '0 0 1 * * *',
        timezone: 'Asia/Shanghai',
      },
      actionDefaults: {
        cleanupType: 'temp_files',
        retentionHours: 24,
      },
      icon: <DeleteOutlined />,
      color: '#8c8c8c',
      difficulty: 'easy',
      tags: ['清理', '临时文件', '维护'],
    },
  ];
};

// 生成模拟任务组数据
const generateMockTaskGroups = (): TaskGroup[] => {
  return [
    {
      id: 'group_data',
      name: '数据处理组',
      description: '所有数据处理相关的定时任务',
      tasks: ['task_0', 'task_1', 'task_2'],
      priority: 'high',
      enabled: true,
      createdAt: Date.now() - 30 * 24 * 60 * 60 * 1000,
    },
    {
      id: 'group_trading',
      name: '交易执行组',
      description: '所有交易相关的定时任务',
      tasks: ['task_3', 'task_4', 'task_5'],
      priority: 'critical',
      enabled: true,
      createdAt: Date.now() - 30 * 24 * 60 * 60 * 1000,
    },
    {
      id: 'group_system',
      name: '系统维护组',
      description: '所有系统维护相关的定时任务',
      tasks: ['task_6', 'task_7', 'task_8'],
      priority: 'medium',
      enabled: true,
      createdAt: Date.now() - 30 * 24 * 60 * 60 * 1000,
    },
  ];
};

// 状态颜色映射
const getStatusColor = (status: string): string => {
  switch (status) {
    case 'pending': return '#1890ff';
    case 'running': return '#52c41a';
    case 'completed': return '#52c41a';
    case 'failed': return '#f5222d';
    case 'cancelled': return '#faad14';
    case 'paused': return '#faad14';
    default: return '#d9d9d9';
  }
};

// 状态描述映射
const getStatusDescription = (status: string): string => {
  switch (status) {
    case 'pending': return '等待中';
    case 'running': return '运行中';
    case 'completed': return '已完成';
    case 'failed': return '失败';
    case 'cancelled': return '已取消';
    case 'paused': return '已暂停';
    default: return '未知';
  }
};

// 优先级颜色映射
const getPriorityColor = (priority: string): string => {
  switch (priority) {
    case 'low': return '#52c41a';
    case 'medium': return '#faad14';
    case 'high': return '#fa8c16';
    case 'critical': return '#f5222d';
    default: return '#d9d9d9';
  }
};

// 优先级描述映射
const getPriorityDescription = (priority: string): string => {
  switch (priority) {
    case 'low': return '低';
    case 'medium': return '中';
    case 'high': return '高';
    case 'critical': return '紧急';
    default: return '未知';
  }
};

// 任务类型描述映射
const getTaskTypeDescription = (type: string): string => {
  switch (type) {
    case 'data_sync': return '数据同步';
    case 'strategy_run': return '策略执行';
    case 'report_generation': return '报告生成';
    case 'system_maintenance': return '系统维护';
    case 'backup': return '备份';
    case 'alert': return '警报';
    case 'notification': return '通知';
    case 'cleanup': return '清理';
    default: return '未知';
  }
};

// 调度类型描述映射
const getScheduleTypeDescription = (type: string): string => {
  switch (type) {
    case 'cron': return 'Cron表达式';
    case 'interval': return '间隔执行';
    case 'once': return '一次性执行';
    case 'calendar': return '日历执行';
    default: return '未知';
  }
};

interface ScheduledTasksProps {
  portfolioId?: string;
  autoRefresh?: boolean;
  onTaskChange?: (tasks: ScheduledTask[]) => void;
}

const ScheduledTasks: React.FC<ScheduledTasksProps> = ({
  portfolioId = 'default',
  autoRefresh = true,
  onTaskChange,
}) => {
  const [tasks, setTasks] = useState<ScheduledTask[]>([]);
  const [templates, setTemplates] = useState<TaskTemplate[]>([]);
  const [groups, setGroups] = useState<TaskGroup[]>([]);
  const [executionHistory, setExecutionHistory] = useState<ExecutionRecord[]>([]);
  const [selectedTask, setSelectedTask] = useState<string | null>(null);
  const [taskModalVisible, setTaskModalVisible] = useState(false);
  const [executionModalVisible, setExecutionModalVisible] = useState(false);
  const [templateModalVisible, setTemplateModalVisible] = useState(false);
  const [groupModalVisible, setGroupModalVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('tasks');
  const [isSystemRunning, setIsSystemRunning] = useState(false);

  // 初始化数据
  useEffect(() => {
    const initializeData = async () => {
      setLoading(true);
      try {
        const mockTasks = generateMockScheduledTasks();
        const mockTemplates = generateMockTaskTemplates();
        const mockGroups = generateMockTaskGroups();
        
        setTasks(mockTasks);
        setTemplates(mockTemplates);
        setGroups(mockGroups);
        
        // 为每个任务生成执行历史
        mockTasks.forEach(task => {
          const history = generateMockExecutionHistory(task.id);
          task.executionHistory = history;
        });
        
        onTaskChange?.(mockTasks);
      } catch (error) {
        console.error('Failed to initialize scheduled tasks data:', error);
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

    const interval = setInterval(() => {
      const mockTasks = generateMockScheduledTasks();
      setTasks(mockTasks);
      
      // 为每个任务生成执行历史
      mockTasks.forEach(task => {
        const history = generateMockExecutionHistory(task.id);
        task.executionHistory = history;
      });
      
      onTaskChange?.(mockTasks);
    }, 15000); // 每15秒刷新一次

    return () => clearInterval(interval);
  }, [autoRefresh, onTaskChange]);

  // 处理任务状态切换
  const handleTaskToggle = useCallback((taskId: string) => {
    setTasks(prev => prev.map(task => 
      task.id === taskId 
        ? { ...task, enabled: !task.enabled, status: !task.enabled ? 'paused' : 'pending' }
        : task
    ));
    onTaskChange?.(tasks.map(task => 
      task.id === taskId 
        ? { ...task, enabled: !task.enabled, status: !task.enabled ? 'paused' : 'pending' }
        : task
    ));
    message.success('任务状态已更新');
  }, [tasks, onTaskChange]);

  // 处理任务立即执行
  const handleTaskExecute = useCallback((taskId: string) => {
    setTasks(prev => prev.map(task => 
      task.id === taskId 
        ? { ...task, status: 'running', running: true }
        : task
    ));
    message.success('任务已开始执行');
  }, []);

  // 处理系统运行状态切换
  const handleSystemToggle = useCallback(() => {
    setIsSystemRunning(!isSystemRunning);
    message.info(isSystemRunning ? '定时任务系统已停止' : '定时任务系统已启动');
  }, [isSystemRunning]);

  // 处理任务创建
  const handleCreateTask = useCallback((values: any) => {
    const newTask: ScheduledTask = {
      id: `task_${Date.now()}`,
      name: values.name,
      description: values.description,
      type: values.type,
      status: 'pending',
      schedule: values.schedule,
      actions: values.actions,
      priority: values.priority,
      retryPolicy: values.retryPolicy,
      timeout: values.timeout,
      maxExecutionTime: values.maxExecutionTime,
      dependencies: values.dependencies,
      executionHistory: [],
      createdAt: Date.now(),
      enabled: values.schedule.enabled,
      running: false,
    };
    
    setTasks(prev => [...prev, newTask]);
    onTaskChange?.([...tasks, newTask]);
    setTaskModalVisible(false);
    message.success('任务创建成功');
  }, [tasks, onTaskChange]);

  // 处理任务组创建
  const handleCreateGroup = useCallback((values: any) => {
    const newGroup: TaskGroup = {
      id: `group_${Date.now()}`,
      name: values.name,
      description: values.description,
      tasks: values.tasks,
      priority: values.priority,
      enabled: values.enabled,
      createdAt: Date.now(),
    };
    
    setGroups(prev => [...prev, newGroup]);
    message.success('任务组创建成功');
  }, []);

  // 任务表格列
  const taskColumns = [
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: ScheduledTask) => (
        <Space>
          {record.running ? <SyncOutlined spin style={{ color: '#1890ff' }} /> : 
           record.enabled ? <CheckCircleOutlined style={{ color: '#52c41a' }} /> : 
           <PauseCircleOutlined style={{ color: '#faad14' }} />}
          <Text strong>{text}</Text>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag>{getTaskTypeDescription(type)}</Tag>
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
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority: string) => (
        <Tag color={getPriorityColor(priority)}>
          {getPriorityDescription(priority)}
        </Tag>
      ),
    },
    {
      title: '调度',
      dataIndex: 'schedule',
      key: 'schedule',
      render: (schedule: ScheduledTask['schedule']) => (
        <Space>
          <Text>{getScheduleTypeDescription(schedule.type)}</Text>
          <Text type="secondary">{schedule.expression}</Text>
        </Space>
      ),
    },
    {
      title: '下次执行',
      dataIndex: 'nextRun',
      key: 'nextRun',
      render: (nextRun?: number) => nextRun ? new Date(nextRun).toLocaleString() : '无',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record: ScheduledTask) => (
        <Space>
          <Switch
            checked={record.enabled}
            onChange={(checked) => handleTaskToggle(record.id)}
            checkedChildren="启用"
            unCheckedChildren="禁用"
          />
          <Button 
            type="link" 
            size="small" 
            onClick={() => handleTaskExecute(record.id)}
            icon={<PlayCircleOutlined />}
          >
            执行
          </Button>
          <Button 
            type="link" 
            size="small" 
            onClick={() => {
              setSelectedTask(record.id);
              setExecutionModalVisible(true);
            }}
          >
            历史
          </Button>
          <Button 
            type="link" 
            size="small" 
            onClick={() => setTaskModalVisible(true)}
          >
            编辑
          </Button>
        </Space>
      ),
    },
  ];

  // 执行历史表格列
  const executionColumns = [
    {
      title: '开始时间',
      dataIndex: 'startTime',
      key: 'startTime',
      render: (timestamp: number) => new Date(timestamp).toLocaleString(),
    },
    {
      title: '结束时间',
      dataIndex: 'endTime',
      key: 'endTime',
      render: (timestamp?: number) => timestamp ? new Date(timestamp).toLocaleString() : '-',
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
      title: '耗时',
      dataIndex: 'duration',
      key: 'duration',
      render: (duration?: number) => duration ? `${(duration / 1000).toFixed(2)}s` : '-',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record: ExecutionRecord) => (
        <Button 
          type="link" 
          size="small" 
          onClick={() => setExecutionModalVisible(true)}
        >
          查看日志
        </Button>
      ),
    },
  ];

  // 模板表格列
  const templateColumns = [
    {
      title: '模板名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: TaskTemplate) => (
        <Space>
          <Avatar size="small" style={{ backgroundColor: record.color }}>
            {record.icon}
          </Avatar>
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
          data: '数据',
          trading: '交易',
          reporting: '报告',
          system: '系统',
          backup: '备份',
          alert: '警报',
        };
        return <Tag>{categoryMap[category as keyof typeof categoryMap]}</Tag>;
      },
    },
    {
      title: '难度',
      dataIndex: 'difficulty',
      key: 'difficulty',
      render: (difficulty: string) => {
        const difficultyMap = {
          easy: '简单',
          medium: '中等',
          hard: '困难',
        };
        const colorMap = {
          easy: '#52c41a',
          medium: '#faad14',
          hard: '#f5222d',
        };
        return <Tag color={colorMap[difficulty as keyof typeof colorMap]}>
          {difficultyMap[difficulty as keyof typeof difficultyMap]}
        </Tag>;
      },
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags: string[]) => (
        <Space>
          {tags.map(tag => <Tag key={tag} size="small">{tag}</Tag>)}
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record: TaskTemplate) => (
        <Button 
          type="link" 
          size="small" 
          onClick={() => {
            setSelectedTask(record.id);
            setTemplateModalVisible(true);
          }}
        >
          使用模板
        </Button>
      ),
    },
  ];

  // 任务组表格列
  const groupColumns = [
    {
      title: '组名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      render: (text: string) => <Text>{text}</Text>,
    },
    {
      title: '任务数量',
      dataIndex: 'tasks',
      key: 'tasks',
      render: (tasks: string[]) => <Badge count={tasks.length} showZero />,
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority: string) => (
        <Tag color={getPriorityColor(priority)}>
          {getPriorityDescription(priority)}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled: boolean) => (
        <Tag color={enabled ? '#52c41a' : '#faad14'}>
          {enabled ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record: TaskGroup) => (
        <Space>
          <Button 
            type="link" 
            size="small" 
            onClick={() => setGroupModalVisible(true)}
          >
            编辑
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
          <Title level={3}>定时任务系统 - {portfolioId}</Title>
          <Paragraph type="secondary">
            智能化定时任务管理，支持多种调度类型和执行策略
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
            <Button icon={<PlusOutlined />} onClick={() => setTaskModalVisible(true)}>
              创建任务
            </Button>
          </Space>
        </Col>
      </Row>

      {/* 系统状态概览 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总任务数"
              value={tasks.length}
              valueStyle={{ color: '#1890ff' }}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="运行中任务"
              value={tasks.filter(t => t.running).length}
              valueStyle={{ color: '#52c41a' }}
              prefix={<SyncOutlined spin />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="启用的任务"
              value={tasks.filter(t => t.enabled).length}
              suffix={`/ ${tasks.length}`}
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="失败任务"
              value={tasks.filter(t => t.status === 'failed').length}
              valueStyle={{ color: '#f5222d' }}
              prefix={<CloseCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 标签页 */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="任务列表" key="tasks">
            <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
              <Col span={24}>
                <Space>
                  <Button 
                    type="primary" 
                    icon={<PlusOutlined />}
                    onClick={() => setTaskModalVisible(true)}
                  >
                    创建任务
                  </Button>
                  <Button icon={<SyncOutlined />} onClick={() => window.location.reload()}>
                    刷新
                  </Button>
                </Space>
              </Col>
            </Row>
            
            <Table
              dataSource={tasks}
              columns={taskColumns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              loading={loading}
              size="small"
            />
          </TabPane>
          
          <TabPane tab="执行历史" key="history">
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
              dataSource={executionHistory}
              columns={executionColumns}
              rowKey="id"
              pagination={{ pageSize: 20 }}
              loading={loading}
              size="small"
            />
          </TabPane>
          
          <TabPane tab="任务模板" key="templates">
            <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
              <Col span={24}>
                <Space>
                  <Button icon={<PlusOutlined />} onClick={() => setTemplateModalVisible(true)}>
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
          
          <TabPane tab="任务组" key="groups">
            <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
              <Col span={24}>
                <Space>
                  <Button 
                    type="primary" 
                    icon={<PlusOutlined />}
                    onClick={() => setGroupModalVisible(true)}
                  >
                    创建组
                  </Button>
                  <Button icon={<SyncOutlined />} onClick={() => window.location.reload()}>
                    刷新
                  </Button>
                </Space>
              </Col>
            </Row>
            
            <Table
              dataSource={groups}
              columns={groupColumns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              loading={loading}
              size="small"
            />
          </TabPane>
        </Tabs>
      </Card>

      {/* 创建任务模态框 */}
      <Modal
        title="创建定时任务"
        open={taskModalVisible}
        onCancel={() => setTaskModalVisible(false)}
        footer={null}
        width={1000}
      >
        <Form
          layout="vertical"
          onFinish={handleCreateTask}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="任务名称"
                name="name"
                rules={[{ required: true, message: '请输入任务名称' }]}
              >
                <Input placeholder="输入任务名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="任务类型"
                name="type"
                rules={[{ required: true, message: '请选择任务类型' }]}
              >
                <Select>
                  <Option value="data_sync">数据同步</Option>
                  <Option value="strategy_run">策略执行</Option>
                  <Option value="report_generation">报告生成</Option>
                  <Option value="system_maintenance">系统维护</Option>
                  <Option value="backup">备份</Option>
                  <Option value="alert">警报</Option>
                  <Option value="notification">通知</Option>
                  <Option value="cleanup">清理</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item
            label="任务描述"
            name="description"
            rules={[{ required: true, message: '请输入任务描述' }]}
          >
            <TextArea rows={3} placeholder="输入任务描述" />
          </Form.Item>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="优先级"
                name="priority"
                rules={[{ required: true, message: '请选择优先级' }]}
              >
                <Select>
                  <Option value="low">低</Option>
                  <Option value="medium">中</Option>
                  <Option value="high">高</Option>
                  <Option value="critical">紧急</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="超时时间"
                name="timeout"
                rules={[{ required: true, message: '请输入超时时间' }]}
              >
                <InputNumber min="1" max="3600" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="调度类型"
                name="schedule.type"
                rules={[{ required: true, message: '请选择调度类型' }]}
              >
                <Select>
                  <Option value="cron">Cron表达式</Option>
                  <Option value="interval">间隔执行</Option>
                  <Option value="once">一次性执行</Option>
                  <Option value="calendar">日历执行</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="调度表达式"
                name="schedule.expression"
                rules={[{ required: true, message: '请输入调度表达式' }]}
              >
                <Input placeholder="输入调度表达式" />
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item
            label="是否启用"
            name="schedule.enabled"
            valuePropName="checked"
          >
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
          
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                创建任务
              </Button>
              <Button onClick={() => setTaskModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 执行历史模态框 */}
      <Modal
        title="执行历史"
        open={executionModalVisible}
        onCancel={() => setExecutionModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedTask && tasks.find(t => t.id === selectedTask)?.executionHistory && (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Text strong>任务：{tasks.find(t => t.id === selectedTask)?.name}</Text>
            <Table
              dataSource={tasks.find(t => t.id === selectedTask)?.executionHistory}
              columns={executionColumns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              size="small"
            />
          </Space>
        )}
      </Modal>

      {/* 任务模板模态框 */}
      <Modal
        title="任务模板"
        open={templateModalVisible}
        onCancel={() => setTemplateModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedTask && templates.find(t => t.id === selectedTask) && (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Row gutter={16}>
              <Col span={12}>
                <Text strong>模板名称：</Text>
                <Text>{templates.find(t => t.id === selectedTask)?.name}</Text>
              </Col>
              <Col span={12}>
                <Text strong>分类：</Text>
                <Text>{templates.find(t => t.id === selectedTask)?.category}</Text>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={12}>
                <Text strong>难度：</Text>
                <Text>{templates.find(t => t.id === selectedTask)?.difficulty}</Text>
              </Col>
              <Col span={12}>
                <Text strong>标签：</Text>
                <Space>
                  {templates.find(t => t.id === selectedTask)?.tags.map(tag => (
                    <Tag key={tag}>{tag}</Tag>
                  ))}
                </Space>
              </Col>
            </Row>
            <Divider />
            <Text strong>模板描述：</Text>
            <Paragraph>{templates.find(t => t.id === selectedTask)?.description}</Paragraph>
            
            <Divider />
            <Text strong>默认调度：</Text>
            <Paragraph>
              类型：{getScheduleTypeDescription(templates.find(t => t.id === selectedTask)?.scheduleDefaults.type || '')}
              <br />
              表达式：{templates.find(t => t.id === selectedTask)?.scheduleDefaults.expression}
            </Paragraph>
            
            <Divider />
            <Text strong>默认动作：</Text>
            <Paragraph>{JSON.stringify(templates.find(t => t.id === selectedTask)?.actionDefaults, null, 2)}</Paragraph>
          </Space>
        )}
      </Modal>

      {/* 任务组模态框 */}
      <Modal
        title="创建任务组"
        open={groupModalVisible}
        onCancel={() => setGroupModalVisible(false)}
        footer={null}
        width={800}
      >
        <Form
          layout="vertical"
          onFinish={handleCreateGroup}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="组名称"
                name="name"
                rules={[{ required: true, message: '请输入组名称' }]}
              >
                <Input placeholder="输入组名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="优先级"
                name="priority"
                rules={[{ required: true, message: '请选择优先级' }]}
              >
                <Select>
                  <Option value="low">低</Option>
                  <Option value="medium">中</Option>
                  <Option value="high">高</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item
            label="组描述"
            name="description"
            rules={[{ required: true, message: '请输入组描述' }]}
          >
            <TextArea rows={3} placeholder="输入组描述" />
          </Form.Item>
          
          <Form.Item
            label="选择任务"
            name="tasks"
            rules={[{ required: true, message: '请选择任务' }]}
          >
            <Select mode="multiple">
              {tasks.map(task => (
                <Option key={task.id} value={task.id}>
                  {task.name}
                </Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item
            label="是否启用"
            name="enabled"
            valuePropName="checked"
          >
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
          
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                创建组
              </Button>
              <Button onClick={() => setGroupModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ScheduledTasks;