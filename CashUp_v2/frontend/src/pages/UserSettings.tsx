/**
 * 用户设置和配置页面
 * User Settings and Configuration Page
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Form,
  Input,
  Switch,
  Select,
  Button,
  Divider,
  Alert,
  Tabs,
  Space,
  Typography,
  Tag,
  List,
  Avatar,
  Modal,
  message,
  Upload,
  InputNumber,
  Slider,
  Radio,
  Checkbox,
  Progress,
  Table,
  Badge,
  Tooltip,
  Popconfirm,
  QRCode,
  notification
} from 'antd';
import {
  UserOutlined,
  SecurityScanOutlined,
  BellOutlined,
  SettingOutlined,
  DatabaseOutlined,
  ApiOutlined,
  MonitorOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  DownloadOutlined,
  UploadOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  MailOutlined,
  PhoneOutlined,
  GlobalOutlined,
  LockOutlined,
  UnlockOutlined,
  KeyOutlined,
  SafetyCertificateOutlined,
  CloudUploadOutlined,
  CloudDownloadOutlined,
  SyncOutlined,
  WarningOutlined
} from '@ant-design/icons';
import type { UploadFile, UploadProps } from 'antd/es/upload';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { TextArea } = Input;
const { Option } = Select;

// 用户配置类型
interface UserConfig {
  id: string;
  username: string;
  email: string;
  phone?: string;
  avatar?: string;
  timezone: string;
  language: string;
  theme: 'light' | 'dark' | 'auto';
  notifications: {
    email: boolean;
    push: boolean;
    sms: boolean;
    tradeAlerts: boolean;
    riskAlerts: boolean;
    systemAlerts: boolean;
    marketing: boolean;
  };
  security: {
    twoFactorEnabled: boolean;
    loginAlerts: boolean;
    sessionTimeout: number;
    passwordPolicy: {
      minLength: number;
      requireUppercase: boolean;
      requireNumbers: boolean;
      requireSpecialChars: boolean;
      expireDays: number;
    };
  };
  trading: {
    defaultExchange: string;
    defaultLeverage: number;
    riskPerTrade: number;
    maxDailyLoss: number;
    maxPositions: number;
    autoStopLoss: boolean;
    autoTakeProfit: boolean;
    slippageTolerance: number;
  };
  api: {
    enabled: boolean;
    rateLimit: number;
    ipWhitelist: string[];
    webhooks: Array<{
      id: string;
      url: string;
      events: string[];
      active: boolean;
    }>;
  };
  data: {
    autoBackup: boolean;
    backupFrequency: 'daily' | 'weekly' | 'monthly';
    retentionPeriod: number;
    exportFormat: 'csv' | 'json' | 'excel';
  };
}

// 交易所配置类型
interface ExchangeConfig {
  id: string;
  name: string;
  type: string;
  apiKey: string;
  apiSecret: string;
  passphrase?: string;
  enabled: boolean;
  testnet: boolean;
  rateLimits: {
    requests: number;
    window: string;
  };
  features: {
    spot: boolean;
    margin: boolean;
    futures: boolean;
    tradingBot: boolean;
  };
  lastSync?: string;
  status: 'connected' | 'disconnected' | 'error';
}

// 系统配置类型
interface SystemConfig {
  version: string;
  build: string;
  environment: 'development' | 'staging' | 'production';
  database: {
    type: string;
    version: string;
    size: string;
    connections: number;
  };
  redis: {
    version: string;
    memory: string;
    connections: number;
  };
  services: Array<{
    name: string;
    status: 'running' | 'stopped' | 'error';
    cpu: number;
    memory: number;
    uptime: string;
  }>;
}

const UserSettings: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('profile');
  const [userConfig, setUserConfig] = useState<UserConfig | null>(null);
  const [exchangeConfigs, setExchangeConfigs] = useState<ExchangeConfig[]>([]);
  const [systemConfig, setSystemConfig] = useState<SystemConfig | null>(null);
  const [passwordVisible, setPasswordVisible] = useState(false);
  const [apiKeysVisible, setApiKeysVisible] = useState<Record<string, boolean>>({});
  const [showQRCode, setShowQRCode] = useState(false);
  const [qrCodeData, setQrCodeData] = useState('');

  // 模拟数据
  const mockUserConfig: UserConfig = {
    id: '1',
    username: 'trader_user',
    email: 'trader@example.com',
    phone: '+86 138 0000 0000',
    avatar: '',
    timezone: 'Asia/Shanghai',
    language: 'zh-CN',
    theme: 'light',
    notifications: {
      email: true,
      push: true,
      sms: false,
      tradeAlerts: true,
      riskAlerts: true,
      systemAlerts: true,
      marketing: false
    },
    security: {
      twoFactorEnabled: true,
      loginAlerts: true,
      sessionTimeout: 3600,
      passwordPolicy: {
        minLength: 8,
        requireUppercase: true,
        requireNumbers: true,
        requireSpecialChars: true,
        expireDays: 90
      }
    },
    trading: {
      defaultExchange: 'binance',
      defaultLeverage: 1,
      riskPerTrade: 2,
      maxDailyLoss: 5,
      maxPositions: 10,
      autoStopLoss: true,
      autoTakeProfit: true,
      slippageTolerance: 0.5
    },
    api: {
      enabled: false,
      rateLimit: 1000,
      ipWhitelist: ['127.0.0.1'],
      webhooks: []
    },
    data: {
      autoBackup: true,
      backupFrequency: 'daily',
      retentionPeriod: 30,
      exportFormat: 'csv'
    }
  };

  const mockExchangeConfigs: ExchangeConfig[] = [
    {
      id: '1',
      name: 'Binance',
      type: 'binance',
      apiKey: '********',
      apiSecret: '********',
      enabled: true,
      testnet: false,
      rateLimits: {
        requests: 1200,
        window: '1m'
      },
      features: {
        spot: true,
        margin: true,
        futures: true,
        tradingBot: true
      },
      lastSync: '2024-01-15T10:30:00Z',
      status: 'connected'
    },
    {
      id: '2',
      name: 'Gate.io',
      type: 'gateio',
      apiKey: '********',
      apiSecret: '********',
      enabled: true,
      testnet: false,
      rateLimits: {
        requests: 100,
        window: '1s'
      },
      features: {
        spot: true,
        margin: true,
        futures: false,
        tradingBot: true
      },
      lastSync: '2024-01-15T10:25:00Z',
      status: 'connected'
    }
  ];

  const mockSystemConfig: SystemConfig = {
    version: '2.0.0',
    build: '2024.01.15',
    environment: 'production',
    database: {
      type: 'PostgreSQL',
      version: '15.4',
      size: '2.3 GB',
      connections: 45
    },
    redis: {
      version: '7.2',
      memory: '512 MB',
      connections: 12
    },
    services: [
      {
        name: 'core-service',
        status: 'running',
        cpu: 15.2,
        memory: 256,
        uptime: '15d 4h 32m'
      },
      {
        name: 'trading-engine',
        status: 'running',
        cpu: 25.8,
        memory: 512,
        uptime: '15d 4h 32m'
      },
      {
        name: 'strategy-platform',
        status: 'running',
        cpu: 18.5,
        memory: 384,
        uptime: '15d 4h 32m'
      },
      {
        name: 'notification-service',
        status: 'running',
        cpu: 8.3,
        memory: 128,
        uptime: '15d 4h 32m'
      }
    ]
  };

  useEffect(() => {
    // 模拟加载数据
    setUserConfig(mockUserConfig);
    setExchangeConfigs(mockExchangeConfigs);
    setSystemConfig(mockSystemConfig);
  }, []);

  const handleSave = async (values: any) => {
    setLoading(true);
    try {
      // 模拟保存
      await new Promise(resolve => setTimeout(resolve, 1000));
      message.success('设置保存成功');
    } catch (error) {
      message.error('保存失败');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (values: any) => {
    setLoading(true);
    try {
      // 模拟密码修改
      await new Promise(resolve => setTimeout(resolve, 1000));
      message.success('密码修改成功');
    } catch (error) {
      message.error('密码修改失败');
    } finally {
      setLoading(false);
    }
  };

  const handleExchangeToggle = async (id: string, enabled: boolean) => {
    try {
      setExchangeConfigs(prev =>
        prev.map(config =>
          config.id === id ? { ...config, enabled } : config
        )
      );
      message.success(`交易所已${enabled ? '启用' : '禁用'}`);
    } catch (error) {
      message.error('操作失败');
    }
  };

  const handleTestConnection = async (id: string) => {
    try {
      // 模拟连接测试
      await new Promise(resolve => setTimeout(resolve, 2000));
      message.success('连接测试成功');
    } catch (error) {
      message.error('连接测试失败');
    }
  };

  const handleEnable2FA = async () => {
    try {
      // 模拟2FA启用
      await new Promise(resolve => setTimeout(resolve, 1000));
      setQrCodeData('otpauth://totp/CashUp:trader_user?secret=JBSWY3DPEHPK3PXP&issuer=CashUp');
      setShowQRCode(true);
    } catch (error) {
      message.error('启用2FA失败');
    }
  };

  const handleDisable2FA = async () => {
    try {
      // 模拟2FA禁用
      await new Promise(resolve => setTimeout(resolve, 1000));
      if (userConfig) {
        setUserConfig({
          ...userConfig,
          security: {
            ...userConfig.security,
            twoFactorEnabled: false
          }
        });
      }
      message.success('2FA已禁用');
    } catch (error) {
      message.error('禁用2FA失败');
    }
  };

  const handleExportData = async (format: string) => {
    try {
      // 模拟数据导出
      await new Promise(resolve => setTimeout(resolve, 1000));
      message.success(`数据导出成功，格式：${format}`);
    } catch (error) {
      message.error('数据导出失败');
    }
  };

  const handleImportData = async (file: UploadFile) => {
    try {
      // 模拟数据导入
      await new Promise(resolve => setTimeout(resolve, 1000));
      message.success('数据导入成功');
    } catch (error) {
      message.error('数据导入失败');
    }
  };

  const uploadProps: UploadProps = {
    name: 'file',
    accept: '.json,.csv,.xlsx',
    beforeUpload: (file) => {
      handleImportData(file);
      return false;
    },
    showUploadList: false
  };

  const renderProfileSettings = () => (
    <Card>
      <Form
        form={form}
        layout="vertical"
        initialValues={userConfig}
        onFinish={handleSave}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="用户名"
              name="username"
              rules={[{ required: true, message: '请输入用户名' }]}
            >
              <Input prefix={<UserOutlined />} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              label="邮箱"
              name="email"
              rules={[{ required: true, type: 'email', message: '请输入有效邮箱' }]}
            >
              <Input prefix={<MailOutlined />} />
            </Form.Item>
          </Col>
        </Row>
        
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="手机号"
              name="phone"
            >
              <Input prefix={<PhoneOutlined />} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              label="时区"
              name="timezone"
            >
              <Select>
                <Option value="Asia/Shanghai">亚洲/上海</Option>
                <Option value="UTC">UTC</Option>
                <Option value="America/New_York">美洲/纽约</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="语言"
              name="language"
            >
              <Select>
                <Option value="zh-CN">简体中文</Option>
                <Option value="en-US">English</Option>
                <Option value="ja-JP">日本語</Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              label="主题"
              name="theme"
            >
              <Select>
                <Option value="light">浅色</Option>
                <Option value="dark">深色</Option>
                <Option value="auto">自动</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            保存设置
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );

  const renderSecuritySettings = () => (
    <div>
      <Card title="密码设置" style={{ marginBottom: 16 }}>
        <Form
          layout="vertical"
          onFinish={handlePasswordChange}
        >
          <Form.Item
            label="当前密码"
            name="currentPassword"
            rules={[{ required: true, message: '请输入当前密码' }]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item
            label="新密码"
            name="newPassword"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 8, message: '密码至少8位' }
            ]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item
            label="确认密码"
            name="confirmPassword"
            dependencies={['newPassword']}
            rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('newPassword') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              修改密码
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="两步验证">
        <Row gutter={16}>
          <Col span={12}>
            <Alert
              message={userConfig?.security.twoFactorEnabled ? '两步验证已启用' : '两步验证未启用'}
              description={
                userConfig?.security.twoFactorEnabled
                  ? '您的账户受到两步验证的保护'
                  : '启用两步验证以提高账户安全性'
              }
              type={userConfig?.security.twoFactorEnabled ? 'success' : 'warning'}
              showIcon
            />
          </Col>
          <Col span={12}>
            <Space>
              {userConfig?.security.twoFactorEnabled ? (
                <Popconfirm
                  title="确定要禁用两步验证吗？"
                  onConfirm={handleDisable2FA}
                  okText="确定"
                  cancelText="取消"
                >
                  <Button danger>禁用两步验证</Button>
                </Popconfirm>
              ) : (
                <Button type="primary" onClick={handleEnable2FA}>
                  启用两步验证
                </Button>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      <Card title="登录安全" style={{ marginTop: 16 }}>
        <Row gutter={16}>
          <Col span={12}>
            <Text>登录提醒</Text>
            <div style={{ marginTop: 8 }}>
              <Switch
                checked={userConfig?.security.loginAlerts}
                onChange={(checked) => {
                  if (userConfig) {
                    setUserConfig({
                      ...userConfig,
                      security: {
                        ...userConfig.security,
                        loginAlerts: checked
                      }
                    });
                  }
                }}
              />
              <Text style={{ marginLeft: 8 }}>
                {userConfig?.security.loginAlerts ? '已启用' : '已禁用'}
              </Text>
            </div>
          </Col>
          <Col span={12}>
            <Text>会话超时</Text>
            <div style={{ marginTop: 8 }}>
              <Select
                value={userConfig?.security.sessionTimeout}
                onChange={(value) => {
                  if (userConfig) {
                    setUserConfig({
                      ...userConfig,
                      security: {
                        ...userConfig.security,
                        sessionTimeout: value
                      }
                    });
                  }
                }}
                style={{ width: '100%' }}
              >
                <Option value={1800}>30分钟</Option>
                <Option value={3600}>1小时</Option>
                <Option value={7200}>2小时</Option>
                <Option value={14400}>4小时</Option>
                <Option value={86400}>24小时</Option>
              </Select>
            </div>
          </Col>
        </Row>
      </Card>
    </div>
  );

  const renderNotificationSettings = () => (
    <Card>
      <Title level={4}>通知设置</Title>
      <Row gutter={16}>
        <Col span={12}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Text>邮件通知</Text>
              <div style={{ marginTop: 8 }}>
                <Switch
                  checked={userConfig?.notifications.email}
                  onChange={(checked) => {
                    if (userConfig) {
                      setUserConfig({
                        ...userConfig,
                        notifications: {
                          ...userConfig.notifications,
                          email: checked
                        }
                      });
                    }
                  }}
                />
                <Text style={{ marginLeft: 8 }}>
                  {userConfig?.notifications.email ? '已启用' : '已禁用'}
                </Text>
              </div>
            </div>
            
            <div>
              <Text>推送通知</Text>
              <div style={{ marginTop: 8 }}>
                <Switch
                  checked={userConfig?.notifications.push}
                  onChange={(checked) => {
                    if (userConfig) {
                      setUserConfig({
                        ...userConfig,
                        notifications: {
                          ...userConfig.notifications,
                          push: checked
                        }
                      });
                    }
                  }}
                />
                <Text style={{ marginLeft: 8 }}>
                  {userConfig?.notifications.push ? '已启用' : '已禁用'}
                </Text>
              </div>
            </div>
            
            <div>
              <Text>短信通知</Text>
              <div style={{ marginTop: 8 }}>
                <Switch
                  checked={userConfig?.notifications.sms}
                  onChange={(checked) => {
                    if (userConfig) {
                      setUserConfig({
                        ...userConfig,
                        notifications: {
                          ...userConfig.notifications,
                          sms: checked
                        }
                      });
                    }
                  }}
                />
                <Text style={{ marginLeft: 8 }}>
                  {userConfig?.notifications.sms ? '已启用' : '已禁用'}
                </Text>
              </div>
            </div>
          </Space>
        </Col>
        
        <Col span={12}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Text>交易提醒</Text>
              <div style={{ marginTop: 8 }}>
                <Switch
                  checked={userConfig?.notifications.tradeAlerts}
                  onChange={(checked) => {
                    if (userConfig) {
                      setUserConfig({
                        ...userConfig,
                        notifications: {
                          ...userConfig.notifications,
                          tradeAlerts: checked
                        }
                      });
                    }
                  }}
                />
                <Text style={{ marginLeft: 8 }}>
                  {userConfig?.notifications.tradeAlerts ? '已启用' : '已禁用'}
                </Text>
              </div>
            </div>
            
            <div>
              <Text>风险提醒</Text>
              <div style={{ marginTop: 8 }}>
                <Switch
                  checked={userConfig?.notifications.riskAlerts}
                  onChange={(checked) => {
                    if (userConfig) {
                      setUserConfig({
                        ...userConfig,
                        notifications: {
                          ...userConfig.notifications,
                          riskAlerts: checked
                        }
                      });
                    }
                  }}
                />
                <Text style={{ marginLeft: 8 }}>
                  {userConfig?.notifications.riskAlerts ? '已启用' : '已禁用'}
                </Text>
              </div>
            </div>
            
            <div>
              <Text>系统提醒</Text>
              <div style={{ marginTop: 8 }}>
                <Switch
                  checked={userConfig?.notifications.systemAlerts}
                  onChange={(checked) => {
                    if (userConfig) {
                      setUserConfig({
                        ...userConfig,
                        notifications: {
                          ...userConfig.notifications,
                          systemAlerts: checked
                        }
                      });
                    }
                  }}
                />
                <Text style={{ marginLeft: 8 }}>
                  {userConfig?.notifications.systemAlerts ? '已启用' : '已禁用'}
                </Text>
              </div>
            </div>
          </Space>
        </Col>
      </Row>
    </Card>
  );

  const renderTradingSettings = () => (
    <Card>
      <Title level={4}>交易设置</Title>
      <Row gutter={16}>
        <Col span={12}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Text>默认交易所</Text>
              <div style={{ marginTop: 8 }}>
                <Select
                  value={userConfig?.trading.defaultExchange}
                  onChange={(value) => {
                    if (userConfig) {
                      setUserConfig({
                        ...userConfig,
                        trading: {
                          ...userConfig.trading,
                          defaultExchange: value
                        }
                      });
                    }
                  }}
                  style={{ width: '100%' }}
                >
                  <Option value="binance">Binance</Option>
                  <Option value="gateio">Gate.io</Option>
                  <Option value="huobi">Huobi</Option>
                </Select>
              </div>
            </div>
            
            <div>
              <Text>默认杠杆</Text>
              <div style={{ marginTop: 8 }}>
                <InputNumber
                  value={userConfig?.trading.defaultLeverage}
                  onChange={(value) => {
                    if (userConfig) {
                      setUserConfig({
                        ...userConfig,
                        trading: {
                          ...userConfig.trading,
                          defaultLeverage: value || 1
                        }
                      });
                    }
                  }}
                  min={1}
                  max={125}
                  style={{ width: '100%' }}
                />
              </div>
            </div>
            
            <div>
              <Text>每笔交易风险</Text>
              <div style={{ marginTop: 8 }}>
                <Slider
                  value={userConfig?.trading.riskPerTrade}
                  onChange={(value) => {
                    if (userConfig) {
                      setUserConfig({
                        ...userConfig,
                        trading: {
                          ...userConfig.trading,
                          riskPerTrade: value as number
                        }
                      });
                    }
                  }}
                  min={0.1}
                  max={10}
                  step={0.1}
                />
                <Text>{userConfig?.trading.riskPerTrade}%</Text>
              </div>
            </div>
          </Space>
        </Col>
        
        <Col span={12}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Text>最大每日亏损</Text>
              <div style={{ marginTop: 8 }}>
                <Slider
                  value={userConfig?.trading.maxDailyLoss}
                  onChange={(value) => {
                    if (userConfig) {
                      setUserConfig({
                        ...userConfig,
                        trading: {
                          ...userConfig.trading,
                          maxDailyLoss: value as number
                        }
                      });
                    }
                  }}
                  min={1}
                  max={20}
                  step={0.5}
                />
                <Text>{userConfig?.trading.maxDailyLoss}%</Text>
              </div>
            </div>
            
            <div>
              <Text>最大持仓数</Text>
              <div style={{ marginTop: 8 }}>
                <InputNumber
                  value={userConfig?.trading.maxPositions}
                  onChange={(value) => {
                    if (userConfig) {
                      setUserConfig({
                        ...userConfig,
                        trading: {
                          ...userConfig.trading,
                          maxPositions: value || 1
                        }
                      });
                    }
                  }}
                  min={1}
                  max={50}
                  style={{ width: '100%' }}
                />
              </div>
            </div>
            
            <div>
              <Text>滑点容忍度</Text>
              <div style={{ marginTop: 8 }}>
                <Slider
                  value={userConfig?.trading.slippageTolerance}
                  onChange={(value) => {
                    if (userConfig) {
                      setUserConfig({
                        ...userConfig,
                        trading: {
                          ...userConfig.trading,
                          slippageTolerance: value as number
                        }
                      });
                    }
                  }}
                  min={0.1}
                  max={2}
                  step={0.1}
                />
                <Text>{userConfig?.trading.slippageTolerance}%</Text>
              </div>
            </div>
          </Space>
        </Col>
      </Row>
      
      <Divider />
      
      <Row gutter={16}>
        <Col span={12}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Text>自动止损</Text>
              <div style={{ marginTop: 8 }}>
                <Switch
                  checked={userConfig?.trading.autoStopLoss}
                  onChange={(checked) => {
                    if (userConfig) {
                      setUserConfig({
                        ...userConfig,
                        trading: {
                          ...userConfig.trading,
                          autoStopLoss: checked
                        }
                      });
                    }
                  }}
                />
                <Text style={{ marginLeft: 8 }}>
                  {userConfig?.trading.autoStopLoss ? '已启用' : '已禁用'}
                </Text>
              </div>
            </div>
          </Space>
        </Col>
        
        <Col span={12}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Text>自动止盈</Text>
              <div style={{ marginTop: 8 }}>
                <Switch
                  checked={userConfig?.trading.autoTakeProfit}
                  onChange={(checked) => {
                    if (userConfig) {
                      setUserConfig({
                        ...userConfig,
                        trading: {
                          ...userConfig.trading,
                          autoTakeProfit: checked
                        }
                      });
                    }
                  }}
                />
                <Text style={{ marginLeft: 8 }}>
                  {userConfig?.trading.autoTakeProfit ? '已启用' : '已禁用'}
                </Text>
              </div>
            </div>
          </Space>
        </Col>
      </Row>
    </Card>
  );

  const renderExchangeSettings = () => (
    <Card>
      <Title level={4}>交易所配置</Title>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />}>
          添加交易所
        </Button>
      </div>
      
      <List
        itemLayout="horizontal"
        dataSource={exchangeConfigs}
        renderItem={(item) => (
          <List.Item
            actions={[
              <Switch
                key="toggle"
                checked={item.enabled}
                onChange={(checked) => handleExchangeToggle(item.id, checked)}
              />,
              <Button
                key="test"
                type="link"
                onClick={() => handleTestConnection(item.id)}
              >
                测试连接
              </Button>,
              <Button
                key="edit"
                type="link"
                icon={<EditOutlined />}
              >
                编辑
              </Button>,
              <Button
                key="delete"
                type="link"
                danger
                icon={<DeleteOutlined />}
              >
                删除
              </Button>
            ]}
          >
            <List.Item.Meta
              avatar={
                <Badge
                  status={item.status === 'connected' ? 'success' : item.status === 'error' ? 'error' : 'default'}
                  text={item.status === 'connected' ? '已连接' : item.status === 'error' ? '错误' : '未连接'}
                />
              }
              title={
                <Space>
                  <Text strong>{item.name}</Text>
                  <Tag color={item.testnet ? 'orange' : 'green'}>
                    {item.testnet ? '测试网' : '主网'}
                  </Tag>
                </Space>
              }
              description={
                <Space>
                  <Text type="secondary">API Key: {item.apiKey}</Text>
                  <Text type="secondary">限流: {item.rateLimits.requests}/{item.rateLimits.window}</Text>
                  {item.lastSync && (
                    <Text type="secondary">最后同步: {dayjs(item.lastSync).format('YYYY-MM-DD HH:mm')}</Text>
                  )}
                </Space>
              }
            />
          </List.Item>
        )}
      />
    </Card>
  );

  const renderAPISettings = () => (
    <Card>
      <Title level={4}>API设置</Title>
      <Row gutter={16}>
        <Col span={12}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Text>启用API访问</Text>
              <div style={{ marginTop: 8 }}>
                <Switch
                  checked={userConfig?.api.enabled}
                  onChange={(checked) => {
                    if (userConfig) {
                      setUserConfig({
                        ...userConfig,
                        api: {
                          ...userConfig.api,
                          enabled: checked
                        }
                      });
                    }
                  }}
                />
                <Text style={{ marginLeft: 8 }}>
                  {userConfig?.api.enabled ? '已启用' : '已禁用'}
                </Text>
              </div>
            </div>
            
            <div>
              <Text>请求限制</Text>
              <div style={{ marginTop: 8 }}>
                <InputNumber
                  value={userConfig?.api.rateLimit}
                  onChange={(value) => {
                    if (userConfig) {
                      setUserConfig({
                        ...userConfig,
                        api: {
                          ...userConfig.api,
                          rateLimit: value || 1000
                        }
                      });
                    }
                  }}
                  min={1}
                  max={10000}
                  style={{ width: '100%' }}
                />
              </div>
            </div>
          </Space>
        </Col>
        
        <Col span={12}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Text>IP白名单</Text>
              <div style={{ marginTop: 8 }}>
                <TextArea
                  value={userConfig?.api.ipWhitelist.join('\n')}
                  onChange={(e) => {
                    if (userConfig) {
                      setUserConfig({
                        ...userConfig,
                        api: {
                          ...userConfig.api,
                          ipWhitelist: e.target.value.split('\n').filter(ip => ip.trim())
                        }
                      });
                    }
                  }}
                  placeholder="每行一个IP地址"
                  rows={4}
                />
              </div>
            </div>
          </Space>
        </Col>
      </Row>
    </Card>
  );

  const renderDataSettings = () => (
    <Card>
      <Title level={4}>数据管理</Title>
      <Row gutter={16}>
        <Col span={12}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Text>自动备份</Text>
              <div style={{ marginTop: 8 }}>
                <Switch
                  checked={userConfig?.data.autoBackup}
                  onChange={(checked) => {
                    if (userConfig) {
                      setUserConfig({
                        ...userConfig,
                        data: {
                          ...userConfig.data,
                          autoBackup: checked
                        }
                      });
                    }
                  }}
                />
                <Text style={{ marginLeft: 8 }}>
                  {userConfig?.data.autoBackup ? '已启用' : '已禁用'}
                </Text>
              </div>
            </div>
            
            <div>
              <Text>备份频率</Text>
              <div style={{ marginTop: 8 }}>
                <Select
                  value={userConfig?.data.backupFrequency}
                  onChange={(value) => {
                    if (userConfig) {
                      setUserConfig({
                        ...userConfig,
                        data: {
                          ...userConfig.data,
                          backupFrequency: value as 'daily' | 'weekly' | 'monthly'
                        }
                      });
                    }
                  }}
                  style={{ width: '100%' }}
                >
                  <Option value="daily">每日</Option>
                  <Option value="weekly">每周</Option>
                  <Option value="monthly">每月</Option>
                </Select>
              </div>
            </div>
            
            <div>
              <Text>保留期限</Text>
              <div style={{ marginTop: 8 }}>
                <InputNumber
                  value={userConfig?.data.retentionPeriod}
                  onChange={(value) => {
                    if (userConfig) {
                      setUserConfig({
                        ...userConfig,
                        data: {
                          ...userConfig.data,
                          retentionPeriod: value || 30
                        }
                      });
                    }
                  }}
                  min={1}
                  max={365}
                  style={{ width: '100%' }}
                />
              </div>
            </div>
          </Space>
        </Col>
        
        <Col span={12}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Text>导出格式</Text>
              <div style={{ marginTop: 8 }}>
                <Select
                  value={userConfig?.data.exportFormat}
                  onChange={(value) => {
                    if (userConfig) {
                      setUserConfig({
                        ...userConfig,
                        data: {
                          ...userConfig.data,
                          exportFormat: value as 'csv' | 'json' | 'excel'
                        }
                      });
                    }
                  }}
                  style={{ width: '100%' }}
                >
                  <Option value="csv">CSV</Option>
                  <Option value="json">JSON</Option>
                  <Option value="excel">Excel</Option>
                </Select>
              </div>
            </div>
            
            <div>
              <Text>数据导出</Text>
              <div style={{ marginTop: 8 }}>
                <Space>
                  <Button
                    icon={<DownloadOutlined />}
                    onClick={() => handleExportData('csv')}
                  >
                    导出CSV
                  </Button>
                  <Button
                    icon={<DownloadOutlined />}
                    onClick={() => handleExportData('json')}
                  >
                    导出JSON
                  </Button>
                  <Button
                    icon={<DownloadOutlined />}
                    onClick={() => handleExportData('excel')}
                  >
                    导出Excel
                  </Button>
                </Space>
              </div>
            </div>
            
            <div>
              <Text>数据导入</Text>
              <div style={{ marginTop: 8 }}>
                <Upload {...uploadProps}>
                  <Button icon={<UploadOutlined />}>
                    导入数据
                  </Button>
                </Upload>
              </div>
            </div>
          </Space>
        </Col>
      </Row>
    </Card>
  );

  const renderSystemSettings = () => (
    <div>
      <Card title="系统信息" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Statistic title="版本" value={systemConfig?.version} />
          </Col>
          <Col span={8}>
            <Statistic title="构建" value={systemConfig?.build} />
          </Col>
          <Col span={8}>
            <Statistic 
              title="环境" 
              value={systemConfig?.environment} 
              valueStyle={{ color: systemConfig?.environment === 'production' ? '#cf1322' : '#3f8600' }}
            />
          </Col>
        </Row>
      </Card>

      <Card title="数据库状态" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Statistic title="类型" value={systemConfig?.database.type} />
          </Col>
          <Col span={6}>
            <Statistic title="版本" value={systemConfig?.database.version} />
          </Col>
          <Col span={6}>
            <Statistic title="大小" value={systemConfig?.database.size} />
          </Col>
          <Col span={6}>
            <Statistic title="连接数" value={systemConfig?.database.connections} />
          </Col>
        </Row>
      </Card>

      <Card title="缓存状态" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Statistic title="版本" value={systemConfig?.redis.version} />
          </Col>
          <Col span={8}>
            <Statistic title="内存" value={systemConfig?.redis.memory} />
          </Col>
          <Col span={8}>
            <Statistic title="连接数" value={systemConfig?.redis.connections} />
          </Col>
        </Row>
      </Card>

      <Card title="服务状态">
        <Table
          dataSource={systemConfig?.services}
          pagination={false}
          size="small"
          columns={[
            {
              title: '服务名称',
              dataIndex: 'name',
              key: 'name',
              render: (text) => <Text strong>{text}</Text>
            },
            {
              title: '状态',
              dataIndex: 'status',
              key: 'status',
              render: (status) => {
                const colors = {
                  running: 'green',
                  stopped: 'red',
                  error: 'orange'
                };
                const texts = {
                  running: '运行中',
                  stopped: '已停止',
                  error: '错误'
                };
                return <Tag color={colors[status]}>{texts[status]}</Tag>;
              }
            },
            {
              title: 'CPU使用率',
              dataIndex: 'cpu',
              key: 'cpu',
              render: (value) => `${value}%`
            },
            {
              title: '内存使用',
              dataIndex: 'memory',
              key: 'memory',
              render: (value) => `${value} MB`
            },
            {
              title: '运行时间',
              dataIndex: 'uptime',
              key: 'uptime',
              render: (text) => <Text type="secondary">{text}</Text>
            }
          ]}
        />
      </Card>
    </div>
  );

  const tabItems = [
    {
      key: 'profile',
      label: '个人资料',
      children: renderProfileSettings()
    },
    {
      key: 'security',
      label: '安全设置',
      children: renderSecuritySettings()
    },
    {
      key: 'notifications',
      label: '通知设置',
      children: renderNotificationSettings()
    },
    {
      key: 'trading',
      label: '交易设置',
      children: renderTradingSettings()
    },
    {
      key: 'exchanges',
      label: '交易所配置',
      children: renderExchangeSettings()
    },
    {
      key: 'api',
      label: 'API设置',
      children: renderAPISettings()
    },
    {
      key: 'data',
      label: '数据管理',
      children: renderDataSettings()
    },
    {
      key: 'system',
      label: '系统设置',
      children: renderSystemSettings()
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Spin spinning={loading}>
        <div style={{ marginBottom: '24px' }}>
          <Title level={2}>用户设置和配置</Title>
          <Text type="secondary">
            管理您的个人资料、安全设置、交易偏好和系统配置
          </Text>
        </div>

        <Card>
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={tabItems}
          />
        </Card>

        <Modal
          title="启用两步验证"
          open={showQRCode}
          onCancel={() => setShowQRCode(false)}
          footer={null}
          width={400}
        >
          <div style={{ textAlign: 'center' }}>
            <Paragraph>
              请使用验证器应用扫描下方二维码：
            </Paragraph>
            <div style={{ margin: '20px 0' }}>
              <QRCode value={qrCodeData} size={200} />
            </div>
            <Paragraph>
              或手动输入密钥：<Text code>JBSWY3DPEHPK3PXP</Text>
            </Paragraph>
            <Paragraph type="secondary">
              扫描完成后，请输入验证器显示的6位数字代码
            </Paragraph>
          </div>
        </Modal>
      </Spin>
    </div>
  );
};

export default UserSettings;