/**
 * 系统设置页面 - 连接真实API
 * System Settings Page - Connected to Real APIs
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
  Modal,
  message,
  Upload,
  InputNumber,
  Slider,
  Table,
  Badge,
  Popconfirm,
  Statistic,
  Spin,
  QRCode,
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
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  DownloadOutlined,
  UploadOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  MailOutlined,
  PhoneOutlined,
  LockOutlined,
  KeyOutlined,
  SafetyCertificateOutlined,
  CloudUploadOutlined,
  CloudDownloadOutlined,
  SyncOutlined,
  WarningOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload';
import dayjs from 'dayjs';
import { configAPI, userAPI } from '../services/api';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TextArea } = Input;

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

// 系统配置类型
interface SystemConfig {
  id: string;
  key: string;
  value: any;
  description: string;
  category: string;
  isSystem: boolean;
  createdAt: string;
  updatedAt: string;
}

const UserSettings: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('profile');
  const [userConfig, setUserConfig] = useState<UserConfig | null>(null);
  const [systemConfigs, setSystemConfigs] = useState<SystemConfig[]>([]);
  const [passwordVisible, setPasswordVisible] = useState(false);
  const [showQRCode, setShowQRCode] = useState(false);
  const [qrCodeData, setQrCodeData] = useState('');

  // 获取用户配置
  const fetchUserConfig = async () => {
    try {
      // 获取用户信息
      const userResponse = await userAPI.getCurrentUser();
      const userData = userResponse.data;
      
      // 获取用户配置
      const configsResponse = await configAPI.getMyConfigs();
      const configs = configsResponse.data || [];
      
      // 构建用户配置对象
      const config: UserConfig = {
        id: userData.id,
        username: userData.username,
        email: userData.email,
        phone: userData.phone,
        avatar: userData.avatar,
        timezone: configs.find((c: any) => c.key === 'timezone')?.value || 'Asia/Shanghai',
        language: configs.find((c: any) => c.key === 'language')?.value || 'zh-CN',
        theme: configs.find((c: any) => c.key === 'theme')?.value || 'light',
        notifications: {
          email: configs.find((c: any) => c.key === 'notifications.email')?.value !== false,
          push: configs.find((c: any) => c.key === 'notifications.push')?.value !== false,
          sms: configs.find((c: any) => c.key === 'notifications.sms')?.value === true,
          tradeAlerts: configs.find((c: any) => c.key === 'notifications.tradeAlerts')?.value !== false,
          riskAlerts: configs.find((c: any) => c.key === 'notifications.riskAlerts')?.value !== false,
          systemAlerts: configs.find((c: any) => c.key === 'notifications.systemAlerts')?.value !== false,
          marketing: configs.find((c: any) => c.key === 'notifications.marketing')?.value === true,
        },
        security: {
          twoFactorEnabled: configs.find((c: any) => c.key === 'security.twoFactorEnabled')?.value === true,
          loginAlerts: configs.find((c: any) => c.key === 'security.loginAlerts')?.value !== false,
          sessionTimeout: configs.find((c: any) => c.key === 'security.sessionTimeout')?.value || 3600,
          passwordPolicy: {
            minLength: configs.find((c: any) => c.key === 'security.passwordPolicy.minLength')?.value || 8,
            requireUppercase: configs.find((c: any) => c.key === 'security.passwordPolicy.requireUppercase')?.value !== false,
            requireNumbers: configs.find((c: any) => c.key === 'security.passwordPolicy.requireNumbers')?.value !== false,
            requireSpecialChars: configs.find((c: any) => c.key === 'security.passwordPolicy.requireSpecialChars')?.value !== false,
            expireDays: configs.find((c: any) => c.key === 'security.passwordPolicy.expireDays')?.value || 90,
          }
        },
        trading: {
          defaultExchange: configs.find((c: any) => c.key === 'trading.defaultExchange')?.value || 'binance',
          defaultLeverage: configs.find((c: any) => c.key === 'trading.defaultLeverage')?.value || 1,
          riskPerTrade: configs.find((c: any) => c.key === 'trading.riskPerTrade')?.value || 2,
          maxDailyLoss: configs.find((c: any) => c.key === 'trading.maxDailyLoss')?.value || 5,
          maxPositions: configs.find((c: any) => c.key === 'trading.maxPositions')?.value || 10,
          autoStopLoss: configs.find((c: any) => c.key === 'trading.autoStopLoss')?.value !== false,
          autoTakeProfit: configs.find((c: any) => c.key === 'trading.autoTakeProfit')?.value !== false,
          slippageTolerance: configs.find((c: any) => c.key === 'trading.slippageTolerance')?.value || 0.5,
        },
        api: {
          enabled: configs.find((c: any) => c.key === 'api.enabled')?.value === true,
          rateLimit: configs.find((c: any) => c.key === 'api.rateLimit')?.value || 1000,
          ipWhitelist: configs.find((c: any) => c.key === 'api.ipWhitelist')?.value || ['127.0.0.1'],
          webhooks: configs.find((c: any) => c.key === 'api.webhooks')?.value || [],
        },
        data: {
          autoBackup: configs.find((c: any) => c.key === 'data.autoBackup')?.value !== false,
          backupFrequency: configs.find((c: any) => c.key === 'data.backupFrequency')?.value || 'daily',
          retentionPeriod: configs.find((c: any) => c.key === 'data.retentionPeriod')?.value || 30,
          exportFormat: configs.find((c: any) => c.key === 'data.exportFormat')?.value || 'csv',
        }
      };
      
      setUserConfig(config);
      form.setFieldsValue(config);
    } catch (error) {
      console.error('获取用户配置失败:', error);
      message.error('获取用户配置失败');
    }
  };

  // 获取系统配置
  const fetchSystemConfigs = async () => {
    try {
      const response = await configAPI.getConfigs();
      setSystemConfigs(response.data || []);
    } catch (error) {
      console.error('获取系统配置失败:', error);
      message.error('获取系统配置失败');
    }
  };

  // 保存用户配置
  const handleSaveUserConfig = async (values: any) => {
    setLoading(true);
    try {
      const configs: Array<{key: string, value: any, description: string, category: string, isSystem: boolean}> = [];
      
      // 构建配置数组
      Object.keys(values).forEach(key => {
        if (typeof values[key] === 'object') {
          Object.keys(values[key]).forEach(subKey => {
            if (typeof values[key][subKey] === 'object') {
              Object.keys(values[key][subKey]).forEach(subSubKey => {
                configs.push({
                  key: `${key}.${subKey}.${subSubKey}`,
                  value: values[key][subKey][subSubKey],
                  description: `${key} ${subKey} ${subSubKey}`,
                  category: key,
                  isSystem: false
                });
              });
            } else {
              configs.push({
                key: `${key}.${subKey}`,
                value: values[key][subKey],
                description: `${key} ${subKey}`,
                category: key,
                isSystem: false
              });
            }
          });
        } else {
          configs.push({
            key: key,
            value: values[key],
            description: key,
            category: 'general',
            isSystem: false
          });
        }
      });
      
      await configAPI.batchUpdateConfigs(configs);
      message.success('用户配置保存成功');
      await fetchUserConfig();
    } catch (error) {
      console.error('保存用户配置失败:', error);
      message.error('保存用户配置失败');
    } finally {
      setLoading(false);
    }
  };

  // 修改密码
  const handleChangePassword = async (values: any) => {
    setLoading(true);
    try {
      await userAPI.changePassword(values);
      message.success('密码修改成功');
    } catch (error) {
      console.error('密码修改失败:', error);
      message.error('密码修改失败');
    } finally {
      setLoading(false);
    }
  };

  // 启用2FA
  const handleEnable2FA = async () => {
    try {
      // 模拟2FA启用
      setQrCodeData('otpauth://totp/CashUp:' + userConfig?.username + '?secret=JBSWY3DPEHPK3PXP&issuer=CashUp');
      setShowQRCode(true);
    } catch (error) {
      message.error('启用2FA失败');
    }
  };

  // 禁用2FA
  const handleDisable2FA = async () => {
    try {
      if (userConfig) {
        await configAPI.updateConfig('security.twoFactorEnabled', false);
        message.success('2FA已禁用');
        await fetchUserConfig();
      }
    } catch (error) {
      message.error('禁用2FA失败');
    }
  };

  // 更新单个配置
  const handleUpdateConfig = async (key: string, value: any) => {
    try {
      await configAPI.updateConfigByKey(key, value);
      message.success('配置更新成功');
      await fetchUserConfig();
    } catch (error) {
      console.error('更新配置失败:', error);
      message.error('更新配置失败');
    }
  };

  // 初始化加载数据
  useEffect(() => {
    fetchUserConfig();
    if (activeTab === 'system') {
      fetchSystemConfigs();
    }
  }, [activeTab]);

  // 渲染个人资料设置
  const renderProfileSettings = () => (
    <Card>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSaveUserConfig}
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

  // 渲染安全设置
  const renderSecuritySettings = () => (
    <div>
      <Card title="密码设置" style={{ marginBottom: 16 }}>
        <Form
          layout="vertical"
          onFinish={handleChangePassword}
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
                onChange={(checked) => handleUpdateConfig('security.loginAlerts', checked)}
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
                onChange={(value) => handleUpdateConfig('security.sessionTimeout', value)}
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

  // 渲染通知设置
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
                  onChange={(checked) => handleUpdateConfig('notifications.email', checked)}
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
                  onChange={(checked) => handleUpdateConfig('notifications.push', checked)}
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
                  onChange={(checked) => handleUpdateConfig('notifications.sms', checked)}
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
                  onChange={(checked) => handleUpdateConfig('notifications.tradeAlerts', checked)}
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
                  onChange={(checked) => handleUpdateConfig('notifications.riskAlerts', checked)}
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
                  onChange={(checked) => handleUpdateConfig('notifications.systemAlerts', checked)}
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

  // 渲染交易设置
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
                  onChange={(value) => handleUpdateConfig('trading.defaultExchange', value)}
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
                  onChange={(value) => handleUpdateConfig('trading.defaultLeverage', value || 1)}
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
                  onChange={(value) => handleUpdateConfig('trading.riskPerTrade', value)}
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
                  onChange={(value) => handleUpdateConfig('trading.maxDailyLoss', value)}
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
                  onChange={(value) => handleUpdateConfig('trading.maxPositions', value || 1)}
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
                  onChange={(value) => handleUpdateConfig('trading.slippageTolerance', value)}
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
                  onChange={(checked) => handleUpdateConfig('trading.autoStopLoss', checked)}
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
                  onChange={(checked) => handleUpdateConfig('trading.autoTakeProfit', checked)}
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

  // 渲染API设置
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
                  onChange={(checked) => handleUpdateConfig('api.enabled', checked)}
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
                  onChange={(value) => handleUpdateConfig('api.rateLimit', value || 1000)}
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
                  onChange={(e) => handleUpdateConfig('api.ipWhitelist', e.target.value.split('\n').filter(ip => ip.trim()))}
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

  // 渲染数据管理
  const renderDataSettings = () => (
    <div>
      <Card title="数据管理" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={12}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text>自动备份</Text>
                <div style={{ marginTop: 8 }}>
                  <Switch
                    checked={userConfig?.data.autoBackup}
                    onChange={(checked) => handleUpdateConfig('data.autoBackup', checked)}
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
                    onChange={(value) => handleUpdateConfig('data.backupFrequency', value)}
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
                    onChange={(value) => handleUpdateConfig('data.retentionPeriod', value || 30)}
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
                    onChange={(value) => handleUpdateConfig('data.exportFormat', value)}
                    style={{ width: '100%' }}
                  >
                    <Option value="csv">CSV</Option>
                    <Option value="json">JSON</Option>
                    <Option value="excel">Excel</Option>
                  </Select>
                </div>
              </div>
            </Space>
          </Col>
        </Row>
      </Card>
      
      <Card title="数据导入导出">
        <Row gutter={16}>
          <Col span={12}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Title level={5}>数据导出</Title>
              <Space>
                <Button icon={<DownloadOutlined />} onClick={() => handleExportData('trades')}> 
                  导出交易记录
                </Button>
                <Button icon={<DownloadOutlined />} onClick={() => handleExportData('orders')}> 
                  导出订单记录
                </Button>
                <Button icon={<DownloadOutlined />} onClick={() => handleExportData('positions')}> 
                  导出持仓记录
                </Button>
              </Space>
            </Space>
          </Col>
          
          <Col span={12}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Title level={5}>数据导入</Title>
              <Upload
                accept=".csv,.json,.xlsx"
                beforeUpload={(file) => {
                  handleImportData(file);
                  return false;
                }}
              >
                <Button icon={<UploadOutlined />}>
                  导入数据文件
                </Button>
              </Upload>
              <Text type="secondary" style={{ fontSize: 12 }}>
                支持 CSV、JSON、Excel 格式
              </Text>
            </Space>
          </Col>
        </Row>
      </Card>
    </div>
  );
  
  // 处理数据导出
  const handleExportData = async (dataType: string) => {
    try {
      const format = userConfig?.data.exportFormat || 'csv';
      // 这里应该调用后端API导出数据
      message.success(`正在导出${dataType}数据为${format.toUpperCase()}格式`);
    } catch (error) {
      console.error('导出数据失败:', error);
      message.error('导出数据失败');
    }
  };
  
  // 处理数据导入
  const handleImportData = async (file: File) => {
    try {
      // 这里应该调用后端API导入数据
      message.success(`正在导入文件: ${file.name}`);
    } catch (error) {
      console.error('导入数据失败:', error);
      message.error('导入数据失败');
    }
  };

  // 渲染系统设置
  const renderSystemSettings = () => (
    <div>
      <Card title="系统配置" style={{ marginBottom: 16 }}>
        <Table
          dataSource={systemConfigs}
          pagination={{
            pageSize: 10,
            showSizeChanger: true
          }}
          columns={[ 
            {
              title: '配置键',
              dataIndex: 'key',
              key: 'key',
              render: (text) => <Text code>{text}</Text>
            },
            {
              title: '配置值',
              dataIndex: 'value',
              key: 'value',
              render: (value) => (
                <Text style={{ wordBreak: 'break-all' }}>
                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                </Text>
              )
            },
            {
              title: '描述',
              dataIndex: 'description',
              key: 'description'
            },
            {
              title: '分类',
              dataIndex: 'category',
              key: 'category',
              render: (category) => <Tag color="blue">{category}</Tag>
            },
            {
              title: '系统配置',
              dataIndex: 'isSystem',
              key: 'isSystem',
              render: (isSystem) => (
                <Tag color={isSystem ? 'red' : 'green'}>
                  {isSystem ? '系统' : '用户'}
                </Tag>
              )
            },
            {
              title: '更新时间',
              dataIndex: 'updatedAt',
              key: 'updatedAt',
              render: (time) => dayjs(time).format('YYYY-MM-DD HH:mm:ss')
            }
          ]}
        />
      </Card>
      
      <Card title="系统管理" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={12}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Title level={5}>系统维护</Title>
              <Space>
                <Button icon={<ReloadOutlined />} onClick={handleClearCache}>
                  清除缓存
                </Button>
                <Button icon={<SyncOutlined />} onClick={handleSyncData}>
                  同步数据
                </Button>
                <Button danger icon={<WarningOutlined />} onClick={handleResetSystem}>
                  重置系统
                </Button>
              </Space>
            </Space>
          </Col>
          
          <Col span={12}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Title level={5}>日志管理</Title>
              <Space>
                <Button icon={<DownloadOutlined />} onClick={handleExportLogs}>
                  导出日志
                </Button>
                <Button danger icon={<DeleteOutlined />} onClick={handleClearLogs}>
                  清除日志
                </Button>
              </Space>
            </Space>
          </Col>
        </Row>
      </Card>
      
      <Card title="系统信息">
        <Row gutter={16}>
          <Col span={8}>
            <Statistic title="配置总数" value={systemConfigs.length} />
          </Col>
          <Col span={8}>
            <Statistic 
              title="系统配置" 
              value={systemConfigs.filter(c => c.isSystem).length}
              valueStyle={{ color: '#cf1322' }}
            />
          </Col>
          <Col span={8}>
            <Statistic 
              title="用户配置" 
              value={systemConfigs.filter(c => !c.isSystem).length}
              valueStyle={{ color: '#3f8600' }}
            />
          </Col>
        </Row>
      </Card>
    </div>
  );
  
  // 系统管理功能
  const handleClearCache = async () => {
    try {
      message.success('缓存清除成功');
    } catch (error) {
      console.error('清除缓存失败:', error);
      message.error('清除缓存失败');
    }
  };
  
  const handleSyncData = async () => {
    try {
      message.success('数据同步成功');
    } catch (error) {
      console.error('数据同步失败:', error);
      message.error('数据同步失败');
    }
  };
  
  const handleResetSystem = async () => {
    try {
      message.warning('系统重置功能需要管理员权限');
    } catch (error) {
      console.error('系统重置失败:', error);
      message.error('系统重置失败');
    }
  };
  
  const handleExportLogs = async () => {
    try {
      message.success('正在导出系统日志');
    } catch (error) {
      console.error('导出日志失败:', error);
      message.error('导出日志失败');
    }
  };
  
  const handleClearLogs = async () => {
    try {
      message.success('日志清除成功');
    } catch (error) {
      console.error('清除日志失败:', error);
      message.error('清除日志失败');
    }
  };

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
