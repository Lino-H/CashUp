import React, { useState } from 'react'
import {
  Card, Button, Space, Typography, Row, Col, Form, Input, Select,
  Switch, Tabs, Divider, Alert, Modal, Upload, Avatar, Slider,
  InputNumber, Checkbox, Radio, Table, Tag, Tooltip
} from 'antd'
import {
  UserOutlined, SettingOutlined, SecurityScanOutlined, BellOutlined,
  KeyOutlined,
  UploadOutlined, EditOutlined, SaveOutlined,
  ExportOutlined, ImportOutlined, DeleteOutlined,
  LockOutlined, UnlockOutlined
} from '@ant-design/icons'

const { Title, Text } = Typography
const { Option } = Select
const { TabPane } = Tabs
const { Password } = Input

interface UserProfile {
  id: string
  username: string
  email: string
  phone: string
  avatar: string
  nickname: string
  timezone: string
  language: string
  theme: string
}

interface APIKey {
  id: string
  name: string
  key: string
  permissions: string[]
  createdAt: string
  lastUsed: string
  status: 'active' | 'disabled'
}

interface SystemConfig {
  maxPositions: number
  maxOrderSize: number
  defaultLeverage: number
  riskLevel: string
  autoBackup: boolean
  dataRetention: number
  sessionTimeout: number
}

const SystemSettings: React.FC = () => {
  const [activeTab, setActiveTab] = useState('profile')
  const [isPasswordModalVisible, setIsPasswordModalVisible] = useState(false)
  const [isAPIKeyModalVisible, setIsAPIKeyModalVisible] = useState(false)
  const [passwordForm] = Form.useForm()
  const [apiKeyForm] = Form.useForm()

  // 模拟数据
  const [userProfile] = useState<UserProfile>({
    id: '1',
    username: 'trader001',
    email: 'trader@example.com',
    phone: '+86 138****8888',
    avatar: 'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20trader%20avatar%20icon%20blue%20theme&image_size=square',
    nickname: '量化交易员',
    timezone: 'Asia/Shanghai',
    language: 'zh-CN',
    theme: 'light'
  })

  const [apiKeys] = useState<APIKey[]>([
    {
      id: '1',
      name: '主要交易API',
      key: 'ak_1234567890abcdef****',
      permissions: ['trading', 'market_data', 'account'],
      createdAt: '2024-12-01 10:30:00',
      lastUsed: '2024-12-19 14:25:00',
      status: 'active'
    },
    {
      id: '2',
      name: '只读API',
      key: 'ak_abcdef1234567890****',
      permissions: ['market_data', 'account'],
      createdAt: '2024-11-15 16:20:00',
      lastUsed: '2024-12-18 09:15:00',
      status: 'active'
    },
    {
      id: '3',
      name: '测试API',
      key: 'ak_test1234567890ab****',
      permissions: ['market_data'],
      createdAt: '2024-10-20 14:10:00',
      lastUsed: '2024-11-30 11:45:00',
      status: 'disabled'
    }
  ])

  const [systemConfig] = useState<SystemConfig>({
    maxPositions: 20,
    maxOrderSize: 100000,
    defaultLeverage: 3,
    riskLevel: 'medium',
    autoBackup: true,
    dataRetention: 365,
    sessionTimeout: 30
  })

  // API密钥表格列配置
  const apiKeyColumns = [
    {
      title: 'API名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: 'API密钥',
      dataIndex: 'key',
      key: 'key',
      render: (text: string) => (
        <div className="flex items-center space-x-2">
          <Text code>{text}</Text>
          <Tooltip title="复制">
            <Button
              type="link"
              size="small"
              onClick={() => navigator.clipboard.writeText(text)}
            >
              复制
            </Button>
          </Tooltip>
        </div>
      )
    },
    {
      title: '权限',
      dataIndex: 'permissions',
      key: 'permissions',
      render: (permissions: string[]) => (
        <div>
          {permissions.map(permission => {
            const permissionConfig = {
              trading: { color: 'red', text: '交易' },
              market_data: { color: 'blue', text: '行情' },
              account: { color: 'green', text: '账户' }
            }
            const config = permissionConfig[permission as keyof typeof permissionConfig]
            return (
              <Tag key={permission} color={config.color}>
                {config.text}
              </Tag>
            )
          })}
        </div>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt'
    },
    {
      title: '最后使用',
      dataIndex: 'lastUsed',
      key: 'lastUsed'
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'red'}>
          {status === 'active' ? '启用' : '禁用'}
        </Tag>
      )
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: APIKey) => (
        <Space>
          <Tooltip title="编辑">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => editAPIKey(record)}
            />
          </Tooltip>
          <Tooltip title={record.status === 'active' ? '禁用' : '启用'}>
            <Button
              type="link"
              size="small"
              icon={record.status === 'active' ? <LockOutlined /> : <UnlockOutlined />}
              onClick={() => toggleAPIKey(record.id)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => deleteAPIKey(record.id)}
            />
          </Tooltip>
        </Space>
      )
    }
  ]

  // 保存用户资料
  const handleSaveProfile = (values: any) => {
    console.log('保存用户资料:', values)
    Modal.success({
      title: '保存成功',
      content: '用户资料已更新'
    })
  }

  // 修改密码
  const handleChangePassword = (values: any) => {
    console.log('修改密码:', values)
    setIsPasswordModalVisible(false)
    passwordForm.resetFields()
    Modal.success({
      title: '密码修改成功',
      content: '请使用新密码重新登录'
    })
  }

  // 创建API密钥
  const handleCreateAPIKey = (values: any) => {
    console.log('创建API密钥:', values)
    setIsAPIKeyModalVisible(false)
    apiKeyForm.resetFields()
    Modal.success({
      title: 'API密钥创建成功',
      content: '请妥善保管您的API密钥'
    })
  }

  // 编辑API密钥
  const editAPIKey = (apiKey: APIKey) => {
    apiKeyForm.setFieldsValue({
      name: apiKey.name,
      permissions: apiKey.permissions
    })
    setIsAPIKeyModalVisible(true)
  }

  // 切换API密钥状态
  const toggleAPIKey = (id: string) => {
    console.log('切换API密钥状态:', id)
  }

  // 删除API密钥
  const deleteAPIKey = (id: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个API密钥吗？此操作不可恢复。',
      onOk: () => {
        console.log('删除API密钥:', id)
      }
    })
  }

  // 保存系统配置
  const handleSaveSystemConfig = (values: any) => {
    console.log('保存系统配置:', values)
    Modal.success({
      title: '配置保存成功',
      content: '系统配置已更新'
    })
  }

  // 导出配置
  const handleExportConfig = () => {
    console.log('导出配置')
    Modal.success({
      title: '导出成功',
      content: '配置文件已下载到本地'
    })
  }

  // 导入配置
  const handleImportConfig = (file: any) => {
    console.log('导入配置:', file)
    return false // 阻止自动上传
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <Title level={2} className="!mb-2">系统设置</Title>
        <Text className="text-gray-500">管理用户资料、安全设置和系统配置</Text>
      </div>

      {/* 主要内容区域 */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          {/* 用户资料 */}
          <TabPane 
            tab={(
              <span>
                <UserOutlined />
                用户资料
              </span>
            )} 
            key="profile"
          >
            <Row gutter={[24, 24]}>
              <Col xs={24} lg={8}>
                <Card title="头像设置" className="text-center">
                  <Avatar size={120} src={userProfile.avatar} className="mb-4" />
                  <br />
                  <Upload
                    showUploadList={false}
                    beforeUpload={() => false}
                  >
                    <Button icon={<UploadOutlined />}>更换头像</Button>
                  </Upload>
                </Card>
              </Col>
              
              <Col xs={24} lg={16}>
                <Card title="基本信息">
                  <Form
                    layout="vertical"
                    initialValues={userProfile}
                    onFinish={handleSaveProfile}
                  >
                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item
                          name="username"
                          label="用户名"
                          rules={[{ required: true, message: '请输入用户名' }]}
                        >
                          <Input disabled />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item
                          name="nickname"
                          label="昵称"
                        >
                          <Input placeholder="请输入昵称" />
                        </Form.Item>
                      </Col>
                    </Row>
                    
                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item
                          name="email"
                          label="邮箱"
                          rules={[
                            { required: true, message: '请输入邮箱' },
                            { type: 'email', message: '请输入有效的邮箱地址' }
                          ]}
                        >
                          <Input placeholder="请输入邮箱" />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item
                          name="phone"
                          label="手机号"
                        >
                          <Input placeholder="请输入手机号" />
                        </Form.Item>
                      </Col>
                    </Row>
                    
                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item
                          name="timezone"
                          label="时区"
                        >
                          <Select placeholder="请选择时区">
                            <Option value="Asia/Shanghai">Asia/Shanghai (UTC+8)</Option>
                            <Option value="America/New_York">America/New_York (UTC-5)</Option>
                            <Option value="Europe/London">Europe/London (UTC+0)</Option>
                            <Option value="Asia/Tokyo">Asia/Tokyo (UTC+9)</Option>
                          </Select>
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item
                          name="language"
                          label="语言"
                        >
                          <Select placeholder="请选择语言">
                            <Option value="zh-CN">简体中文</Option>
                            <Option value="en-US">English</Option>
                            <Option value="ja-JP">日本語</Option>
                            <Option value="ko-KR">한국어</Option>
                          </Select>
                        </Form.Item>
                      </Col>
                    </Row>
                    
                    <Form.Item
                      name="theme"
                      label="主题"
                    >
                      <Radio.Group>
                        <Radio value="light">浅色主题</Radio>
                        <Radio value="dark">深色主题</Radio>
                        <Radio value="auto">跟随系统</Radio>
                      </Radio.Group>
                    </Form.Item>
                    
                    <Form.Item className="mb-0">
                      <Button type="primary" htmlType="submit" icon={<SaveOutlined />}>
                        保存资料
                      </Button>
                    </Form.Item>
                  </Form>
                </Card>
              </Col>
            </Row>
          </TabPane>
          
          {/* 安全设置 */}
          <TabPane 
            tab={(
              <span>
                <SecurityScanOutlined />
                安全设置
              </span>
            )} 
            key="security"
          >
            <Row gutter={[24, 24]}>
              <Col xs={24} lg={12}>
                <Card title="密码安全">
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <Text strong>登录密码</Text>
                        <br />
                        <Text className="text-gray-500">上次修改：2024-11-15</Text>
                      </div>
                      <Button 
                        type="primary" 
                        onClick={() => setIsPasswordModalVisible(true)}
                      >
                        修改密码
                      </Button>
                    </div>
                    
                    <Divider />
                    
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span>双因素认证 (2FA)</span>
                        <Switch defaultChecked />
                      </div>
                      <div className="flex justify-between items-center">
                        <span>登录短信验证</span>
                        <Switch />
                      </div>
                      <div className="flex justify-between items-center">
                        <span>异地登录提醒</span>
                        <Switch defaultChecked />
                      </div>
                    </div>
                  </div>
                </Card>
              </Col>
              
              <Col xs={24} lg={12}>
                <Card title="会话管理">
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span>会话超时时间</span>
                      <Select defaultValue={30} style={{ width: 120 }}>
                        <Option value={15}>15分钟</Option>
                        <Option value={30}>30分钟</Option>
                        <Option value={60}>1小时</Option>
                        <Option value={120}>2小时</Option>
                      </Select>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span>自动锁定屏幕</span>
                      <Switch defaultChecked />
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span>记住登录状态</span>
                      <Switch defaultChecked />
                    </div>
                    
                    <Divider />
                    
                    <Button type="primary" danger block>
                      注销所有设备
                    </Button>
                  </div>
                </Card>
              </Col>
            </Row>
            
            {/* API密钥管理 */}
            <Card title="API密钥管理" className="mt-6">
              <div className="mb-4 flex justify-between items-center">
                <Alert
                  message="API密钥安全提醒"
                  description="请妥善保管您的API密钥，不要在不安全的环境中使用。建议定期更换密钥以确保安全。"
                  type="warning"
                  showIcon
                  closable
                />
                <Button 
                  type="primary" 
                  icon={<KeyOutlined />}
                  onClick={() => setIsAPIKeyModalVisible(true)}
                >
                  创建API密钥
                </Button>
              </div>
              
              <Table
                columns={apiKeyColumns}
                dataSource={apiKeys}
                rowKey="id"
                pagination={false}
                className="data-table"
                scroll={{ x: 1000 }}
              />
            </Card>
          </TabPane>
          
          {/* 系统配置 */}
          <TabPane 
            tab={(
              <span>
                <SettingOutlined />
                系统配置
              </span>
            )} 
            key="system"
          >
            <Row gutter={[24, 24]}>
              <Col xs={24} lg={12}>
                <Card title="交易设置">
                  <Form
                    layout="vertical"
                    initialValues={systemConfig}
                    onFinish={handleSaveSystemConfig}
                  >
                    <Form.Item
                      name="maxPositions"
                      label="最大持仓数量"
                      tooltip="同时持有的最大仓位数量"
                    >
                      <Slider
                        min={1}
                        max={50}
                        marks={{
                          1: '1',
                          10: '10',
                          20: '20',
                          30: '30',
                          50: '50'
                        }}
                      />
                    </Form.Item>
                    
                    <Form.Item
                      name="maxOrderSize"
                      label="单笔最大订单金额 (USD)"
                    >
                      <InputNumber
                        style={{ width: '100%' }}
                        min={1000}
                        max={1000000}
                        step={1000}
                        formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                        parser={(value: string | undefined) => value ? parseInt(value.replace(/\$\s?|(,*)/g, '')) || 0 : 0}
                      />
                    </Form.Item>
                    
                    <Form.Item
                      name="defaultLeverage"
                      label="默认杠杆倍数"
                    >
                      <Select>
                        <Option value={1}>1x</Option>
                        <Option value={2}>2x</Option>
                        <Option value={3}>3x</Option>
                        <Option value={5}>5x</Option>
                        <Option value={10}>10x</Option>
                      </Select>
                    </Form.Item>
                    
                    <Form.Item
                      name="riskLevel"
                      label="风险等级"
                    >
                      <Radio.Group>
                        <Radio value="low">保守</Radio>
                        <Radio value="medium">平衡</Radio>
                        <Radio value="high">激进</Radio>
                      </Radio.Group>
                    </Form.Item>
                    
                    <Form.Item className="mb-0">
                      <Button type="primary" htmlType="submit" icon={<SaveOutlined />}>
                        保存配置
                      </Button>
                    </Form.Item>
                  </Form>
                </Card>
              </Col>
              
              <Col xs={24} lg={12}>
                <Card title="数据管理">
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <Text strong>自动备份</Text>
                        <br />
                        <Text className="text-gray-500">每日自动备份交易数据</Text>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span>数据保留期限</span>
                      <Select defaultValue={365} style={{ width: 120 }}>
                        <Option value={90}>3个月</Option>
                        <Option value={180}>6个月</Option>
                        <Option value={365}>1年</Option>
                        <Option value={730}>2年</Option>
                      </Select>
                    </div>
                    
                    <Divider />
                    
                    <div className="space-y-2">
                      <Button 
                        type="primary" 
                        icon={<ExportOutlined />} 
                        block
                        onClick={handleExportConfig}
                      >
                        导出配置
                      </Button>
                      
                      <Upload
                        beforeUpload={handleImportConfig}
                        showUploadList={false}
                      >
                        <Button icon={<ImportOutlined />} block>
                          导入配置
                        </Button>
                      </Upload>
                      
                      <Button 
                        danger 
                        icon={<DeleteOutlined />} 
                        block
                        onClick={() => {
                          Modal.confirm({
                            title: '确认清理',
                            content: '确定要清理历史数据吗？此操作不可恢复。',
                            onOk: () => console.log('清理历史数据')
                          })
                        }}
                      >
                        清理历史数据
                      </Button>
                    </div>
                  </div>
                </Card>
              </Col>
            </Row>
          </TabPane>
          
          {/* 通知设置 */}
          <TabPane 
            tab={(
              <span>
                <BellOutlined />
                通知设置
              </span>
            )} 
            key="notifications"
          >
            <Card title="通知偏好设置">
              <div className="space-y-6">
                <div>
                  <Title level={4}>交易通知</Title>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span>订单执行通知</span>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex justify-between items-center">
                      <span>持仓变化通知</span>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex justify-between items-center">
                      <span>盈亏提醒</span>
                      <Switch />
                    </div>
                  </div>
                </div>
                
                <Divider />
                
                <div>
                  <Title level={4}>风险通知</Title>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span>保证金不足警告</span>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex justify-between items-center">
                      <span>止损触发通知</span>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex justify-between items-center">
                      <span>风险限制触发</span>
                      <Switch defaultChecked />
                    </div>
                  </div>
                </div>
                
                <Divider />
                
                <div>
                  <Title level={4}>系统通知</Title>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span>系统维护通知</span>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex justify-between items-center">
                      <span>功能更新通知</span>
                      <Switch />
                    </div>
                    <div className="flex justify-between items-center">
                      <span>安全提醒</span>
                      <Switch defaultChecked />
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </TabPane>
        </Tabs>
      </Card>

      {/* 修改密码模态框 */}
      <Modal
        title="修改密码"
        open={isPasswordModalVisible}
        onCancel={() => {
          setIsPasswordModalVisible(false)
          passwordForm.resetFields()
        }}
        footer={null}
        width={500}
      >
        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={handleChangePassword}
        >
          <Form.Item
            name="currentPassword"
            label="当前密码"
            rules={[{ required: true, message: '请输入当前密码' }]}
          >
            <Password placeholder="请输入当前密码" />
          </Form.Item>
          
          <Form.Item
            name="newPassword"
            label="新密码"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 8, message: '密码长度至少8位' },
              { pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, message: '密码必须包含大小写字母和数字' }
            ]}
          >
            <Password placeholder="请输入新密码" />
          </Form.Item>
          
          <Form.Item
            name="confirmPassword"
            label="确认新密码"
            dependencies={['newPassword']}
            rules={[
              { required: true, message: '请确认新密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('newPassword') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'))
                }
              })
            ]}
          >
            <Password placeholder="请再次输入新密码" />
          </Form.Item>
          
          <Form.Item className="mb-0 text-right">
            <Space>
              <Button onClick={() => {
                setIsPasswordModalVisible(false)
                passwordForm.resetFields()
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                确认修改
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* API密钥模态框 */}
      <Modal
        title="创建API密钥"
        open={isAPIKeyModalVisible}
        onCancel={() => {
          setIsAPIKeyModalVisible(false)
          apiKeyForm.resetFields()
        }}
        footer={null}
        width={500}
      >
        <Form
          form={apiKeyForm}
          layout="vertical"
          onFinish={handleCreateAPIKey}
        >
          <Form.Item
            name="name"
            label="API名称"
            rules={[{ required: true, message: '请输入API名称' }]}
          >
            <Input placeholder="请输入API名称" />
          </Form.Item>
          
          <Form.Item
            name="permissions"
            label="权限设置"
            rules={[{ required: true, message: '请选择权限' }]}
          >
            <Checkbox.Group>
              <Space direction="vertical">
                <Checkbox value="trading">交易权限</Checkbox>
                <Checkbox value="market_data">行情数据</Checkbox>
                <Checkbox value="account">账户信息</Checkbox>
              </Space>
            </Checkbox.Group>
          </Form.Item>
          
          <Alert
            message="安全提醒"
            description="API密钥创建后将只显示一次，请妥善保管。建议定期更换密钥以确保安全。"
            type="warning"
            showIcon
            className="mb-4"
          />
          
          <Form.Item className="mb-0 text-right">
            <Space>
              <Button onClick={() => {
                setIsAPIKeyModalVisible(false)
                apiKeyForm.resetFields()
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                创建密钥
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default SystemSettings