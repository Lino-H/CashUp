/**
 * 报告自动化组件
 * Automated Reporting Component
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
  Upload,
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
  FileOutlined,
  FilePdfOutlined,
  FileExcelOutlined,
  FileWordOutlined,
  FileImageOutlined,
  DownloadOutlined,
  SendOutlined,
  EyeOutlined as EyeOutlined2,
  EditOutlined as EditOutlined2,
  DeleteOutlined as DeleteOutlined2,
  PlusOutlined as PlusOutlined2,
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { RadioGroup } = Radio;
const { TabPane } = Tabs;
const { TextArea } = Input;
const { Step } = Steps;

// 报告自动化类型定义
export interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  type: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly' | 'custom';
  category: 'trading' | 'performance' | 'risk' | 'portfolio' | 'market' | 'custom';
  format: 'pdf' | 'excel' | 'word' | 'html' | 'csv';
  sections: ReportSection[];
  schedule: {
    frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly' | 'custom';
    cronExpression?: string;
    sendTime: string;
    daysOfWeek?: number[];
    daysOfMonth?: number[];
    monthsOfYear?: number[];
  };
  recipients: {
    email: string[];
    push: string[];
    webhook?: string;
  };
  settings: {
    includeCharts: boolean;
    includeTables: boolean;
    includeAnalysis: boolean;
    includeRecommendations: boolean;
    language: 'zh-CN' | 'en-US';
    timezone: string;
  };
  createdAt: number;
  updatedAt: number;
  author: string;
  lastGenerated?: number;
  generatedCount: number;
  tags: string[];
}

export interface ReportSection {
  id: string;
  name: string;
  type: 'summary' | 'performance' | 'risk' | 'trades' | 'portfolio' | 'market' | 'custom';
  enabled: boolean;
  dataSources: string[];
  chartTypes: string[];
  tableColumns: string[];
  customContent?: string;
  order: number;
}

export interface ReportInstance {
  id: string;
  templateId: string;
  templateName: string;
  status: 'draft' | 'generating' | 'completed' | 'failed' | 'cancelled' | 'scheduled';
  progress: number;
  scheduledTime: number;
  generatedTime?: number;
  completedTime?: number;
  format: 'pdf' | 'excel' | 'word' | 'html' | 'csv';
  fileSize?: number;
  downloadUrl?: string;
  previewUrl?: string;
  recipients: {
    email: string[];
    push: string[];
    webhook?: string;
  };
  deliveryStatus: {
    email: 'pending' | 'sent' | 'failed';
    push: 'pending' | 'sent' | 'failed';
    webhook?: 'pending' | 'sent' | 'failed';
  };
  error?: string;
}

export interface ReportHistory {
  id: string;
  templateId: string;
  templateName: string;
  generatedTime: number;
  format: string;
  fileSize: number;
  downloadUrl: string;
  previewUrl?: string;
  status: 'success' | 'failed';
  error?: string;
}

export interface NotificationTemplate {
  id: string;
  name: string;
  type: 'email' | 'push' | 'sms' | 'webhook';
  template: string;
  variables: string[];
  channelConfig: {
    smtp?: {
      host: string;
      port: number;
      username: string;
      password: string;
      from: string;
    };
    push?: {
      service: string;
      apiKey: string;
      apiSecret: string;
    };
    sms?: {
      provider: string;
      apiKey: string;
      apiSecret: string;
    };
    webhook?: {
      url: string;
      method: 'GET' | 'POST';
      headers?: { [key: string]: string };
      payload?: { [key: string]: any };
    };
  };
  createdAt: number;
  updatedAt: number;
  testCount: number;
}

// 生成模拟报告模板数据
const generateMockReportTemplates = (): ReportTemplate[] => {
  const templates: ReportTemplate[] = [];
  const types = ['daily', 'weekly', 'monthly', 'quarterly', 'yearly', 'custom'] as const;
  const categories = ['trading', 'performance', 'risk', 'portfolio', 'market', 'custom'] as const;
  const formats = ['pdf', 'excel', 'word', 'html', 'csv'] as const;
  
  for (let i = 0; i < 8; i++) {
    templates.push({
      id: `template_${i}`,
      name: `报告模板_${i + 1}`,
      description: `这是第${i + 1}个报告模板的描述`,
      type: types[i % types.length],
      category: categories[i % categories.length],
      format: formats[i % formats.length],
      sections: [
        {
          id: 'summary',
          name: '执行摘要',
          type: 'summary',
          enabled: true,
          dataSources: ['portfolio', 'market'],
          chartTypes: ['line', 'bar'],
          tableColumns: ['date', 'value', 'change'],
          order: 1,
        },
        {
          id: 'performance',
          name: '业绩分析',
          type: 'performance',
          enabled: true,
          dataSources: ['trades', 'portfolio'],
          chartTypes: ['line', 'area'],
          tableColumns: ['date', 'pnl', 'return'],
          order: 2,
        },
      ],
      schedule: {
        frequency: ['daily', 'weekly', 'monthly', 'quarterly', 'yearly', 'custom'][i % 6] as any,
        cronExpression: i % 6 === 0 ? '0 9 * * *' : i % 6 === 1 ? '0 9 * * 1' : i % 6 === 2 ? '0 9 1 * *' : i % 6 === 3 ? '0 9 1 1,4,7,10 *' : i % 6 === 4 ? '0 9 1 1 *' : '0 9 * * *',
        sendTime: '09:00',
        daysOfWeek: [1, 2, 3, 4, 5],
        daysOfMonth: [1, 15],
        monthsOfYear: [1, 4, 7, 10],
      },
      recipients: {
        email: ['admin@example.com', 'user@example.com'],
        push: ['device1', 'device2'],
        webhook: 'https://example.com/webhook',
      },
      settings: {
        includeCharts: true,
        includeTables: true,
        includeAnalysis: true,
        includeRecommendations: true,
        language: 'zh-CN',
        timezone: 'Asia/Shanghai',
      },
      createdAt: Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000,
      updatedAt: Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000,
      author: `Author_${Math.floor(Math.random() * 10) + 1}`,
      lastGenerated: Math.random() > 0.3 ? Date.now() - Math.random() * 24 * 60 * 60 * 1000 : undefined,
      generatedCount: Math.floor(Math.random() * 100),
      tags: ['交易', '业绩', '风险'],
    });
  }
  
  return templates;
};

// 生成模拟报告实例数据
const generateMockReportInstances = (): ReportInstance[] => {
  const instances: ReportInstance[] = [];
  const templates = generateMockReportTemplates();
  const statuses = ['draft', 'generating', 'completed', 'failed', 'cancelled', 'scheduled'] as const;
  const formats = ['pdf', 'excel', 'word', 'html', 'csv'] as const;
  
  for (let i = 0; i < 20; i++) {
    const template = templates[i % templates.length];
    instances.push({
      id: `instance_${i}`,
      templateId: template.id,
      templateName: template.name,
      status: statuses[Math.floor(Math.random() * statuses.length)],
      progress: Math.random() * 100,
      scheduledTime: Date.now() - Math.random() * 24 * 60 * 60 * 1000,
      generatedTime: Math.random() > 0.5 ? Date.now() - Math.random() * 24 * 60 * 60 * 1000 : undefined,
      completedTime: Math.random() > 0.5 ? Date.now() - Math.random() * 24 * 60 * 60 * 1000 : undefined,
      format: formats[Math.floor(Math.random() * formats.length)],
      fileSize: Math.random() * 10 + 1,
      downloadUrl: `/reports/download/${i}`,
      previewUrl: `/reports/preview/${i}`,
      recipients: {
        email: ['admin@example.com', 'user@example.com'],
        push: ['device1', 'device2'],
        webhook: 'https://example.com/webhook',
      },
      deliveryStatus: {
        email: Math.random() > 0.3 ? 'sent' : 'pending',
        push: Math.random() > 0.3 ? 'sent' : 'pending',
        webhook: Math.random() > 0.3 ? 'sent' : 'pending',
      },
      error: Math.random() > 0.8 ? '生成报告时发生错误' : undefined,
    });
  }
  
  return instances.sort((a, b) => b.scheduledTime - a.scheduledTime);
};

// 生成模拟报告历史数据
const generateMockReportHistory = (): ReportHistory[] => {
  const history: ReportHistory[] = [];
  const formats = ['pdf', 'excel', 'word', 'html', 'csv'] as const;
  
  for (let i = 0; i < 50; i++) {
    history.push({
      id: `history_${i}`,
      templateId: `template_${i % 8}`,
      templateName: `报告模板_${(i % 8) + 1}`,
      generatedTime: Date.now() - (i + 1) * 24 * 60 * 60 * 1000,
      format: formats[Math.floor(Math.random() * formats.length)],
      fileSize: Math.random() * 10 + 1,
      downloadUrl: `/reports/download/history/${i}`,
      previewUrl: `/reports/preview/history/${i}`,
      status: Math.random() > 0.2 ? 'success' : 'failed',
      error: Math.random() > 0.8 ? '生成报告时发生错误' : undefined,
    });
  }
  
  return history.sort((a, b) => b.generatedTime - a.generatedTime);
};

// 生成模拟通知模板数据
const generateMockNotificationTemplates = (): NotificationTemplate[] => {
  return [
    {
      id: 'template_email',
      name: '邮件通知模板',
      type: 'email',
      template: '尊敬的用户，您的报告已生成完成，请查收附件。',
      variables: ['reportName', 'generatedTime', 'downloadUrl'],
      channelConfig: {
        smtp: {
          host: 'smtp.example.com',
          port: 587,
          username: 'user@example.com',
          password: 'password',
          from: 'noreply@example.com',
        },
      },
      createdAt: Date.now() - 30 * 24 * 60 * 60 * 1000,
      updatedAt: Date.now() - 7 * 24 * 60 * 60 * 1000,
      testCount: 10,
    },
    {
      id: 'template_push',
      name: '推送通知模板',
      type: 'push',
      template: '您的报告已生成完成，点击查看详情。',
      variables: ['reportName', 'generatedTime', 'previewUrl'],
      channelConfig: {
        push: {
          service: 'firebase',
          apiKey: 'your-api-key',
          apiSecret: 'your-api-secret',
        },
      },
      createdAt: Date.now() - 30 * 24 * 60 * 60 * 1000,
      updatedAt: Date.now() - 7 * 24 * 60 * 60 * 1000,
      testCount: 5,
    },
    {
      id: 'template_webhook',
      name: 'Webhook通知模板',
      type: 'webhook',
      template: '{ "report": "${reportName}", "time": "${generatedTime}" }',
      variables: ['reportName', 'generatedTime'],
      channelConfig: {
        webhook: {
          url: 'https://example.com/webhook',
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer your-token',
          },
          payload: {
            event: 'report_generated',
            data: {
              reportName: '${reportName}',
              generatedTime: '${generatedTime}',
              downloadUrl: '${downloadUrl}',
            },
          },
        },
      },
      createdAt: Date.now() - 30 * 24 * 60 * 60 * 1000,
      updatedAt: Date.now() - 7 * 24 * 60 * 60 * 1000,
      testCount: 3,
    },
  ];
};

// 状态颜色映射
const getStatusColor = (status: string): string => {
  switch (status) {
    case 'draft': return '#d9d9d9';
    case 'generating': return '#1890ff';
    case 'completed': return '#52c41a';
    case 'failed': return '#f5222d';
    case 'cancelled': return '#faad14';
    case 'scheduled': return '#722ed1';
    case 'success': return '#52c41a';
    case 'pending': return '#faad14';
    case 'sent': return '#52c41a';
    default: return '#d9d9d9';
  }
};

// 状态描述映射
const getStatusDescription = (status: string): string => {
  switch (status) {
    case 'draft': return '草稿';
    case 'generating': return '生成中';
    case 'completed': return '已完成';
    case 'failed': return '失败';
    case 'cancelled': return '已取消';
    case 'scheduled': return '已调度';
    case 'success': return '成功';
    case 'pending': return '等待中';
    case 'sent': return '已发送';
    default: return '未知';
  }
};

// 报告类型描述映射
const getReportTypeDescription = (type: string): string => {
  switch (type) {
    case 'daily': return '日报';
    case 'weekly': return '周报';
    case 'monthly': return '月报';
    case 'quarterly': return '季报';
    case 'yearly': return '年报';
    case 'custom': return '自定义';
    default: return '未知';
  }
};

// 报告分类描述映射
const getReportCategoryDescription = (category: string): string => {
  switch (category) {
    case 'trading': return '交易';
    case 'performance': return '业绩';
    case 'risk': return '风险';
    case 'portfolio': return '投资组合';
    case 'market': return '市场';
    case 'custom': return '自定义';
    default: return '未知';
  }
};

// 报告格式图标映射
const getFormatIcon = (format: string): React.ReactNode => {
  switch (format) {
    case 'pdf': return <FilePdfOutlined />;
    case 'excel': return <FileExcelOutlined />;
    case 'word': return <FileWordOutlined />;
    case 'html': return <FileOutlined />;
    case 'csv': return <FileExcelOutlined />;
    default: return <FileOutlined />;
  }
};

interface AutomatedReportingProps {
  portfolioId?: string;
  autoRefresh?: boolean;
  onTemplateChange?: (templates: ReportTemplate[]) => void;
  onInstanceChange?: (instances: ReportInstance[]) => void;
}

const AutomatedReporting: React.FC<AutomatedReportingProps> = ({
  portfolioId = 'default',
  autoRefresh = true,
  onTemplateChange,
  onInstanceChange,
}) => {
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [instances, setInstances] = useState<ReportInstance[]>([]);
  const [history, setHistory] = useState<ReportHistory[]>([]);
  const [notificationTemplates, setNotificationTemplates] = useState<NotificationTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [selectedInstance, setSelectedInstance] = useState<string | null>(null);
  const [templateModalVisible, setTemplateModalVisible] = useState(false);
  const [instanceModalVisible, setInstanceModalVisible] = useState(false);
  const [notificationModalVisible, setNotificationModalVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('templates');
  const [isSystemRunning, setIsSystemRunning] = useState(false);

  // 初始化数据
  useEffect(() => {
    const initializeData = async () => {
      setLoading(true);
      try {
        const mockTemplates = generateMockReportTemplates();
        const mockInstances = generateMockReportInstances();
        const mockHistory = generateMockReportHistory();
        const mockNotificationTemplates = generateMockNotificationTemplates();
        
        setTemplates(mockTemplates);
        setInstances(mockInstances);
        setHistory(mockHistory);
        setNotificationTemplates(mockNotificationTemplates);
        
        onTemplateChange?.(mockTemplates);
        onInstanceChange?.(mockInstances);
      } catch (error) {
        console.error('Failed to initialize automated reporting data:', error);
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
      const mockInstances = generateMockReportInstances();
      const mockHistory = generateMockReportHistory();
      
      setInstances(mockInstances);
      setHistory(mockHistory);
      
      onInstanceChange?.(mockInstances);
    }, 20000); // 每20秒刷新一次

    return () => clearInterval(interval);
  }, [autoRefresh, onInstanceChange]);

  // 处理系统运行状态切换
  const handleSystemToggle = useCallback(() => {
    setIsSystemRunning(!isSystemRunning);
    message.info(isSystemRunning ? '报告自动化系统已停止' : '报告自动化系统已启动');
  }, [isSystemRunning]);

  // 处理模板创建
  const handleCreateTemplate = useCallback((values: any) => {
    const newTemplate: ReportTemplate = {
      id: `template_${Date.now()}`,
      name: values.name,
      description: values.description,
      type: values.type,
      category: values.category,
      format: values.format,
      sections: values.sections,
      schedule: values.schedule,
      recipients: values.recipients,
      settings: values.settings,
      createdAt: Date.now(),
      updatedAt: Date.now(),
      author: '当前用户',
      generatedCount: 0,
      tags: values.tags || [],
    };
    
    setTemplates(prev => [...prev, newTemplate]);
    onTemplateChange?.([...templates, newTemplate]);
    setTemplateModalVisible(false);
    message.success('报告模板创建成功');
  }, [templates, onTemplateChange]);

  // 处理实例生成
  const handleGenerateInstance = useCallback((templateId: string) => {
    const template = templates.find(t => t.id === templateId);
    if (!template) return;
    
    const newInstance: ReportInstance = {
      id: `instance_${Date.now()}`,
      templateId: template.id,
      templateName: template.name,
      status: 'generating',
      progress: 0,
      scheduledTime: Date.now(),
      format: template.format,
      recipients: template.recipients,
      deliveryStatus: {
        email: 'pending',
        push: 'pending',
        webhook: 'pending',
      },
    };
    
    setInstances(prev => [newInstance, ...prev]);
    onInstanceChange?.([newInstance, ...instances]);
    message.success('报告已开始生成');
  }, [templates, instances, onInstanceChange]);

  // 处理下载报告
  const handleDownloadReport = useCallback((instance: ReportInstance) => {
    if (instance.downloadUrl) {
      // 模拟下载
      const link = document.createElement('a');
      link.href = instance.downloadUrl;
      link.download = `${instance.templateName}_${new Date().toISOString()}.${instance.format}`;
      link.click();
      message.success('报告下载已开始');
    }
  }, []);

  // 模板表格列
  const templateColumns = [
    {
      title: '模板名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: ReportTemplate) => (
        <Space>
          <Avatar size="small" icon={<FileOutlined />} />
          <Text strong>{text}</Text>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag>{getReportTypeDescription(type)}</Tag>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => (
        <Tag>{getReportCategoryDescription(category)}</Tag>
      ),
    },
    {
      title: '格式',
      dataIndex: 'format',
      key: 'format',
      render: (format: string) => (
        <Space>
          {getFormatIcon(format)}
          <Text>{format.toUpperCase()}</Text>
        </Space>
      ),
    },
    {
      title: '生成次数',
      dataIndex: 'generatedCount',
      key: 'generatedCount',
      render: (count: number) => (
        <Text>{count}</Text>
      ),
    },
    {
      title: '上次生成',
      dataIndex: 'lastGenerated',
      key: 'lastGenerated',
      render: (timestamp?: number) => timestamp ? new Date(timestamp).toLocaleString() : '无',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record: ReportTemplate) => (
        <Space>
          <Button 
            type="link" 
            size="small" 
            onClick={() => handleGenerateInstance(record.id)}
          >
            生成
          </Button>
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
            onClick={() => setTemplateModalVisible(true)}
          >
            编辑
          </Button>
        </Space>
      ),
    },
  ];

  // 实例表格列
  const instanceColumns = [
    {
      title: '报告名称',
      dataIndex: 'templateName',
      key: 'templateName',
      render: (text: string) => <Text strong>{text}</Text>,
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
      title: '格式',
      dataIndex: 'format',
      key: 'format',
      render: (format: string) => (
        <Space>
          {getFormatIcon(format)}
          <Text>{format.toUpperCase()}</Text>
        </Space>
      ),
    },
    {
      title: '文件大小',
      dataIndex: 'fileSize',
      key: 'fileSize',
      render: (size?: number) => size ? `${size.toFixed(2)} MB` : '-',
    },
    {
      title: '调度时间',
      dataIndex: 'scheduledTime',
      key: 'scheduledTime',
      render: (timestamp: number) => new Date(timestamp).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record: ReportInstance) => (
        <Space>
          {record.status === 'completed' && (
            <Button 
              type="link" 
              size="small" 
              icon={<DownloadOutlined />}
              onClick={() => handleDownloadReport(record)}
            >
              下载
            </Button>
          )}
          <Button 
            type="link" 
            size="small" 
            onClick={() => setSelectedInstance(record.id)}
          >
            详情
          </Button>
        </Space>
      ),
    },
  ];

  // 历史表格列
  const historyColumns = [
    {
      title: '报告名称',
      dataIndex: 'templateName',
      key: 'templateName',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: '生成时间',
      dataIndex: 'generatedTime',
      key: 'generatedTime',
      render: (timestamp: number) => new Date(timestamp).toLocaleString(),
    },
    {
      title: '格式',
      dataIndex: 'format',
      key: 'format',
      render: (format: string) => (
        <Space>
          {getFormatIcon(format)}
          <Text>{format.toUpperCase()}</Text>
        </Space>
      ),
    },
    {
      title: '文件大小',
      dataIndex: 'fileSize',
      key: 'fileSize',
      render: (size: number) => `${size.toFixed(2)} MB`,
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
      title: '操作',
      key: 'action',
      render: (_, record: ReportHistory) => (
        <Button 
          type="link" 
          size="small" 
          icon={<DownloadOutlined />}
          onClick={() => {
            const link = document.createElement('a');
            link.href = record.downloadUrl;
            link.download = `${record.templateName}_${new Date(record.generatedTime).toISOString()}.${record.format}`;
            link.click();
            message.success('报告下载已开始');
          }}
        >
          下载
        </Button>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      {/* 标题和控制 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={16}>
          <Title level={3}>报告自动化 - {portfolioId}</Title>
          <Paragraph type="secondary">
            智能化报告生成和分发，支持多种格式和自定义模板
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
            <Button icon={<PlusOutlined />} onClick={() => setTemplateModalVisible(true)}>
              创建模板
            </Button>
          </Space>
        </Col>
      </Row>

      {/* 系统状态概览 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="报告模板"
              value={templates.length}
              valueStyle={{ color: '#1890ff' }}
              prefix={<FileOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="生成中报告"
              value={instances.filter(i => i.status === 'generating').length}
              valueStyle={{ color: '#1890ff' }}
              prefix={<SyncOutlined spin />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已完成报告"
              value={instances.filter(i => i.status === 'completed').length}
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="今日生成"
              value={history.filter(h => 
                new Date(h.generatedTime).toDateString() === new Date().toDateString()
              ).length}
              valueStyle={{ color: '#722ed1' }}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 标签页 */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="报告模板" key="templates">
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
          
          <TabPane tab="报告实例" key="instances">
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
              dataSource={instances}
              columns={instanceColumns}
              rowKey="id"
              pagination={{ pageSize: 20 }}
              loading={loading}
              size="small"
            />
          </TabPane>
          
          <TabPane tab="历史记录" key="history">
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
              dataSource={history}
              columns={historyColumns}
              rowKey="id"
              pagination={{ pageSize: 30 }}
              loading={loading}
              size="small"
            />
          </TabPane>
          
          <TabPane tab="通知模板" key="notifications">
            <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
              <Col span={24}>
                <Space>
                  <Button 
                    type="primary" 
                    icon={<PlusOutlined />}
                    onClick={() => setNotificationModalVisible(true)}
                  >
                    创建模板
                  </Button>
                  <Button icon={<SyncOutlined />} onClick={() => window.location.reload()}>
                    刷新
                  </Button>
                </Space>
              </Col>
            </Row>
            
            <List
              dataSource={notificationTemplates}
              renderItem={(template) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={
                      <Avatar 
                        style={{ backgroundColor: template.type === 'email' ? '#1890ff' : template.type === 'push' ? '#52c41a' : '#722ed1' }}
                        icon={template.type === 'email' ? <SendOutlined /> : template.type === 'push' ? <BellOutlined /> : <ApiOutlined />}
                      />
                    }
                    title={
                      <Space>
                        <Text strong>{template.name}</Text>
                        <Tag>{template.type}</Tag>
                        <Text type="secondary">测试次数: {template.testCount}</Text>
                      </Space>
                    }
                    description={
                      <Space>
                        <Text>{template.template}</Text>
                        <Button 
                          type="link" 
                          size="small" 
                          onClick={() => setNotificationModalVisible(true)}
                        >
                          编辑
                        </Button>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </TabPane>
        </Tabs>
      </Card>

      {/* 创建报告模板模态框 */}
      <Modal
        title="创建报告模板"
        open={templateModalVisible}
        onCancel={() => setTemplateModalVisible(false)}
        footer={null}
        width={1200}
      >
        <Form
          layout="vertical"
          onFinish={handleCreateTemplate}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="模板名称"
                name="name"
                rules={[{ required: true, message: '请输入模板名称' }]}
              >
                <Input placeholder="输入模板名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="报告类型"
                name="type"
                rules={[{ required: true, message: '请选择报告类型' }]}
              >
                <Select>
                  <Option value="daily">日报</Option>
                  <Option value="weekly">周报</Option>
                  <Option value="monthly">月报</Option>
                  <Option value="quarterly">季报</Option>
                  <Option value="yearly">年报</Option>
                  <Option value="custom">自定义</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="报告分类"
                name="category"
                rules={[{ required: true, message: '请选择报告分类' }]}
              >
                <Select>
                  <Option value="trading">交易</Option>
                  <Option value="performance">业绩</Option>
                  <Option value="risk">风险</Option>
                  <Option value="portfolio">投资组合</Option>
                  <Option value="market">市场</Option>
                  <Option value="custom">自定义</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="报告格式"
                name="format"
                rules={[{ required: true, message: '请选择报告格式' }]}
              >
                <Select>
                  <Option value="pdf">PDF</Option>
                  <Option value="excel">Excel</Option>
                  <Option value="word">Word</Option>
                  <Option value="html">HTML</Option>
                  <Option value="csv">CSV</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item
            label="模板描述"
            name="description"
            rules={[{ required: true, message: '请输入模板描述' }]}
          >
            <TextArea rows={3} placeholder="输入模板描述" />
          </Form.Item>
          
          <Form.Item
            label="报告章节"
            name="sections"
            rules={[{ required: true, message: '请配置报告章节' }]}
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <Form.Item name="sections.summary" valuePropName="checked">
                <Checkbox>执行摘要</Checkbox>
              </Form.Item>
              <Form.Item name="sections.performance" valuePropName="checked">
                <Checkbox>业绩分析</Checkbox>
              </Form.Item>
              <Form.Item name="sections.risk" valuePropName="checked">
                <Checkbox>风险分析</Checkbox>
              </Form.Item>
              <Form.Item name="sections.trades" valuePropName="checked">
                <Checkbox>交易明细</Checkbox>
              </Form.Item>
            </Space>
          </Form.Item>
          
          <Form.Item
            label="发送时间"
            name="schedule.sendTime"
            rules={[{ required: true, message: '请输入发送时间' }]}
          >
            <TimePicker format="HH:mm" style={{ width: '100%' }} />
          </Form.Item>
          
          <Form.Item
            label="收件人"
            name="recipients.email"
            rules={[{ required: true, message: '请输入收件人邮箱' }]}
          >
            <Select mode="tags" placeholder="输入邮箱地址" style={{ width: '100%' }} />
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

      {/* 报告模板详情模态框 */}
      <Modal
        title="报告模板详情"
        open={!!selectedTemplate}
        onCancel={() => setSelectedTemplate(null)}
        footer={null}
        width={800}
      >
        {selectedTemplate && templates.find(t => t.id === selectedTemplate) && (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Row gutter={16}>
              <Col span={12}>
                <Text strong>模板名称：</Text>
                <Text>{templates.find(t => t.id === selectedTemplate)?.name}</Text>
              </Col>
              <Col span={12}>
                <Text strong>报告类型：</Text>
                <Text>{getReportTypeDescription(templates.find(t => t.id === selectedTemplate)?.type || '')}</Text>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={12}>
                <Text strong>报告分类：</Text>
                <Text>{getReportCategoryDescription(templates.find(t => t.id === selectedTemplate)?.category || '')}</Text>
              </Col>
              <Col span={12}>
                <Text strong>报告格式：</Text>
                <Text>{(templates.find(t => t.id === selectedTemplate)?.format || '').toUpperCase()}</Text>
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
            <Row gutter={16}>
              <Col span={12}>
                <Text strong>生成次数：</Text>
                <Text>{templates.find(t => t.id === selectedTemplate)?.generatedCount}</Text>
              </Col>
              <Col span={12}>
                <Text strong>上次生成：</Text>
                <Text>{templates.find(t => t.id === selectedTemplate)?.lastGenerated ? new Date(templates.find(t => t.id === selectedTemplate)?.lastGenerated || 0).toLocaleString() : '无'}</Text>
              </Col>
            </Row>
            <Divider />
            <Text strong>模板描述：</Text>
            <Paragraph>{templates.find(t => t.id === selectedTemplate)?.description}</Paragraph>
            
            <Divider />
            <Text strong>调度设置：</Text>
            <Paragraph>
              频率：{getReportTypeDescription(templates.find(t => t.id === selectedTemplate)?.schedule.frequency || '')}
              <br />
              发送时间：{templates.find(t => t.id === selectedTemplate)?.schedule.sendTime}
            </Paragraph>
            
            <Divider />
            <Text strong>收件人：</Text>
            <Paragraph>
              邮箱：{(templates.find(t => t.id === selectedTemplate)?.recipients.email || []).join(', ')}
              <br />
              推送：{(templates.find(t => t.id === selectedTemplate)?.recipients.push || []).join(', ')}
            </Paragraph>
            
            <Divider />
            <Text strong>报告章节：</Text>
            <Space>
              {templates.find(t => t.id === selectedTemplate)?.sections.map(section => (
                <Tag key={section.id}>{section.name}</Tag>
              ))}
            </Space>
          </Space>
        )}
      </Modal>

      {/* 报告实例详情模态框 */}
      <Modal
        title="报告实例详情"
        open={!!selectedInstance}
        onCancel={() => setSelectedInstance(null)}
        footer={null}
        width={800}
      >
        {selectedInstance && instances.find(i => i.id === selectedInstance) && (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Row gutter={16}>
              <Col span={12}>
                <Text strong>报告名称：</Text>
                <Text>{instances.find(i => i.id === selectedInstance)?.templateName}</Text>
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
                <Text strong>调度时间：</Text>
                <Text>{new Date(instances.find(i => i.id === selectedInstance)?.scheduledTime || 0).toLocaleString()}</Text>
              </Col>
              <Col span={12}>
                <Text strong>完成时间：</Text>
                <Text>{instances.find(i => i.id === selectedInstance)?.completedTime ? new Date(instances.find(i => i.id === selectedInstance)?.completedTime || 0).toLocaleString() : '未完成'}</Text>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={12}>
                <Text strong>文件格式：</Text>
                <Text>{(instances.find(i => i.id === selectedInstance)?.format || '').toUpperCase()}</Text>
              </Col>
              <Col span={12}>
                <Text strong>文件大小：</Text>
                <Text>{instances.find(i => i.id === selectedInstance)?.fileSize ? `${instances.find(i => i.id === selectedInstance)?.fileSize?.toFixed(2)} MB` : '未知'}</Text>
              </Col>
            </Row>
            
            <Divider />
            <Text strong>分发状态：</Text>
            <Row gutter={16}>
              <Col span={8}>
                <Text>邮件：</Text>
                <Tag color={getStatusColor(instances.find(i => i.id === selectedInstance)?.deliveryStatus.email || '')}>
                  {getStatusDescription(instances.find(i => i.id === selectedInstance)?.deliveryStatus.email || '')}
                </Tag>
              </Col>
              <Col span={8}>
                <Text>推送：</Text>
                <Tag color={getStatusColor(instances.find(i => i.id === selectedInstance)?.deliveryStatus.push || '')}>
                  {getStatusDescription(instances.find(i => i.id === selectedInstance)?.deliveryStatus.push || '')}
                </Tag>
              </Col>
              <Col span={8}>
                <Text>Webhook：</Text>
                <Tag color={getStatusColor(instances.find(i => i.id === selectedInstance)?.deliveryStatus.webhook || '')}>
                  {getStatusDescription(instances.find(i => i.id === selectedInstance)?.deliveryStatus.webhook || '')}
                </Tag>
              </Col>
            </Row>
            
            {instances.find(i => i.id === selectedInstance)?.error && (
              <>
                <Divider />
                <Text strong>错误信息：</Text>
                <Alert
                  message="生成错误"
                  description={instances.find(i => i.id === selectedInstance)?.error}
                  type="error"
                  showIcon
                />
              </>
            )}
          </Space>
        )}
      </Modal>
    </div>
  );
};

export default AutomatedReporting;