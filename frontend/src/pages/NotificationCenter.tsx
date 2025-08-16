import React, { useState } from 'react'
import {
  Card, Table, Button, Space, Tag, Typography, Row, Col, Statistic,
  Select, Input, Modal, Form, Switch, Alert, Badge, Tabs,
  Tooltip, Divider, Checkbox, TimePicker, InputNumber
} from 'antd'
import {
  BellOutlined, MailOutlined, MessageOutlined, SettingOutlined,
  ReloadOutlined, DeleteOutlined, EyeOutlined, CheckOutlined,
  InfoCircleOutlined, WarningOutlined,
  CloseCircleOutlined, SoundOutlined, MobileOutlined, DesktopOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { Option } = Select
const { TabPane } = Tabs
const { TextArea } = Input

interface Notification {
  id: string
  type: 'system' | 'trading' | 'risk' | 'strategy' | 'market'
  level: 'info' | 'warning' | 'error' | 'success'
  title: string
  content: string
  isRead: boolean
  createdAt: string
  source?: string
  actionUrl?: string
}

interface NotificationSettings {
  id: string
  category: string
  name: string
  description: string
  email: boolean
  push: boolean
  sms: boolean
  inApp: boolean
}

interface NotificationStats {
  total: number
  unread: number
  today: number
  thisWeek: number
}

const NotificationCenter: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('notifications')
  const [selectedType, setSelectedType] = useState('all')
  const [isSettingsModalVisible, setIsSettingsModalVisible] = useState(false)
  const [isComposeModalVisible, setIsComposeModalVisible] = useState(false)
  const [selectedNotifications, setSelectedNotifications] = useState<string[]>([])
  const [form] = Form.useForm()

  // 模拟数据
  const [notificationStats] = useState<NotificationStats>({
    total: 156,
    unread: 23,
    today: 12,
    thisWeek: 45
  })

  const [notifications] = useState<Notification[]>([
    {
      id: '1',
      type: 'risk',
      level: 'warning',
      title: 'BTC/USDT持仓风险预警',
      content: '您的BTC/USDT持仓未实现亏损已达到-5.2%，接近止损线，请及时关注。',
      isRead: false,
      createdAt: '2024-12-19 14:30:00',
      source: '风险管理系统',
      actionUrl: '/risk-management'
    },
    {
      id: '2',
      type: 'trading',
      level: 'success',
      title: '订单执行成功',
      content: '您的ETH/USDT限价买入订单已成功执行，成交价格：$2,680.50',
      isRead: false,
      createdAt: '2024-12-19 13:45:00',
      source: '交易系统'
    },
    {
      id: '3',
      type: 'strategy',
      level: 'info',
      title: '策略表现报告',
      content: '趋势跟踪策略A本周收益率为+3.2%，表现良好。',
      isRead: true,
      createdAt: '2024-12-19 12:20:00',
      source: '策略管理系统',
      actionUrl: '/strategy-management'
    },
    {
      id: '4',
      type: 'market',
      level: 'info',
      title: '市场分析更新',
      content: 'BTC突破关键阻力位$43,000，技术指标显示继续上涨趋势。',
      isRead: true,
      createdAt: '2024-12-19 11:30:00',
      source: '市场分析系统',
      actionUrl: '/market-analysis'
    },
    {
      id: '5',
      type: 'system',
      level: 'error',
      title: '系统维护通知',
      content: '系统将于今晚22:00-23:00进行维护，期间可能影响交易功能。',
      isRead: false,
      createdAt: '2024-12-19 10:15:00',
      source: '系统管理'
    },
    {
      id: '6',
      type: 'trading',
      level: 'warning',
      title: '保证金不足警告',
      content: '您的账户保证金使用率已达到75%，建议及时补充资金。',
      isRead: true,
      createdAt: '2024-12-19 09:30:00',
      source: '交易系统'
    }
  ])

  const [notificationSettings] = useState<NotificationSettings[]>([
    {
      id: '1',
      category: '交易通知',
      name: '订单执行',
      description: '订单成交、取消等状态变化通知',
      email: true,
      push: true,
      sms: false,
      inApp: true
    },
    {
      id: '2',
      category: '交易通知',
      name: '持仓变化',
      description: '开仓、平仓、强制平仓等通知',
      email: true,
      push: true,
      sms: true,
      inApp: true
    },
    {
      id: '3',
      category: '风险管理',
      name: '风险预警',
      description: '保证金不足、止损触发等风险提醒',
      email: true,
      push: true,
      sms: true,
      inApp: true
    },
    {
      id: '4',
      category: '风险管理',
      name: '限制触发',
      description: '风险限制触发、账户限制等通知',
      email: true,
      push: false,
      sms: true,
      inApp: true
    },
    {
      id: '5',
      category: '策略管理',
      name: '策略状态',
      description: '策略启停、异常等状态变化通知',
      email: false,
      push: true,
      sms: false,
      inApp: true
    },
    {
      id: '6',
      category: '策略管理',
      name: '策略表现',
      description: '策略收益报告、表现分析等通知',
      email: true,
      push: false,
      sms: false,
      inApp: true
    },
    {
      id: '7',
      category: '市场信息',
      name: '价格预警',
      description: '价格突破、技术指标信号等市场提醒',
      email: false,
      push: true,
      sms: false,
      inApp: true
    },
    {
      id: '8',
      category: '系统通知',
      name: '系统维护',
      description: '系统升级、维护等重要通知',
      email: true,
      push: true,
      sms: false,
      inApp: true
    }
  ])

  // 通知表格列配置
  const notificationColumns = [
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 80,
      render: (type: string) => {
        const typeConfig = {
          system: { color: 'blue', text: '系统', icon: <SettingOutlined /> },
          trading: { color: 'green', text: '交易', icon: <MessageOutlined /> },
          risk: { color: 'red', text: '风险', icon: <WarningOutlined /> },
          strategy: { color: 'purple', text: '策略', icon: <BellOutlined /> },
          market: { color: 'orange', text: '市场', icon: <InfoCircleOutlined /> }
        }
        const config = typeConfig[type as keyof typeof typeConfig]
        return (
          <Tooltip title={config.text}>
            <Tag color={config.color} icon={config.icon}>
              {config.text}
            </Tag>
          </Tooltip>
        )
      }
    },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      width: 80,
      render: (level: string) => {
        const levelConfig = {
          info: { color: 'blue', text: '信息', icon: <InfoCircleOutlined /> },
          success: { color: 'green', text: '成功', icon: <CheckOutlined /> },
          warning: { color: 'orange', text: '警告', icon: <WarningOutlined /> },
          error: { color: 'red', text: '错误', icon: <CloseCircleOutlined /> }
        }
        const config = levelConfig[level as keyof typeof levelConfig]
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        )
      }
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      render: (text: string, record: Notification) => (
        <div className="flex items-center space-x-2">
          {!record.isRead && <Badge status="processing" />}
          <Text strong={!record.isRead}>{text}</Text>
        </div>
      )
    },
    {
      title: '内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      width: 120
    },
    {
      title: '时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 150,
      render: (text: string) => (
        <Tooltip title={text}>
          <Text>{dayjs(text).fromNow()}</Text>
        </Tooltip>
      )
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: Notification) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => viewNotification(record)}
            />
          </Tooltip>
          {!record.isRead && (
            <Tooltip title="标记已读">
              <Button
                type="link"
                size="small"
                icon={<CheckOutlined />}
                onClick={() => markAsRead([record.id])}
              />
            </Tooltip>
          )}
          <Tooltip title="删除">
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => deleteNotification(record.id)}
            />
          </Tooltip>
        </Space>
      )
    }
  ]

  // 通知设置表格列配置
  const settingsColumns = [
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 100
    },
    {
      title: '通知名称',
      dataIndex: 'name',
      key: 'name',
      width: 120,
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description'
    },
    {
      title: '邮件',
      dataIndex: 'email',
      key: 'email',
      width: 80,
      render: (checked: boolean, record: NotificationSettings) => (
        <Switch
          checked={checked}
          size="small"
          onChange={(value) => updateSetting(record.id, 'email', value)}
        />
      )
    },
    {
      title: '推送',
      dataIndex: 'push',
      key: 'push',
      width: 80,
      render: (checked: boolean, record: NotificationSettings) => (
        <Switch
          checked={checked}
          size="small"
          onChange={(value) => updateSetting(record.id, 'push', value)}
        />
      )
    },
    {
      title: '短信',
      dataIndex: 'sms',
      key: 'sms',
      width: 80,
      render: (checked: boolean, record: NotificationSettings) => (
        <Switch
          checked={checked}
          size="small"
          onChange={(value) => updateSetting(record.id, 'sms', value)}
        />
      )
    },
    {
      title: '应用内',
      dataIndex: 'inApp',
      key: 'inApp',
      width: 80,
      render: (checked: boolean, record: NotificationSettings) => (
        <Switch
          checked={checked}
          size="small"
          onChange={(value) => updateSetting(record.id, 'inApp', value)}
        />
      )
    }
  ]

  // 过滤通知
  const filteredNotifications = notifications.filter(notification => {
    if (selectedType === 'all') return true
    if (selectedType === 'unread') return !notification.isRead
    return notification.type === selectedType
  })

  // 查看通知详情
  const viewNotification = (notification: Notification) => {
    Modal.info({
      title: notification.title,
      content: (
        <div className="space-y-3">
          <div>
            <Text strong>类型：</Text>
            <Tag color="blue" className="ml-2">{notification.type}</Tag>
          </div>
          <div>
            <Text strong>级别：</Text>
            <Tag color="orange" className="ml-2">{notification.level}</Tag>
          </div>
          <div>
            <Text strong>内容：</Text>
            <p className="mt-1">{notification.content}</p>
          </div>
          {notification.source && (
            <div>
              <Text strong>来源：</Text>
              <span className="ml-2">{notification.source}</span>
            </div>
          )}
          <div>
            <Text strong>时间：</Text>
            <span className="ml-2">{notification.createdAt}</span>
          </div>
        </div>
      ),
      width: 500
    })
    
    // 标记为已读
    if (!notification.isRead) {
      markAsRead([notification.id])
    }
  }

  // 标记已读
  const markAsRead = (ids: string[]) => {
    console.log('标记已读:', ids)
  }

  // 删除通知
  const deleteNotification = (id: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这条通知吗？',
      onOk: () => {
        console.log('删除通知:', id)
      }
    })
  }

  // 批量操作
  const handleBatchAction = (action: 'read' | 'delete') => {
    if (selectedNotifications.length === 0) {
      Modal.warning({
        title: '请选择通知',
        content: '请先选择要操作的通知'
      })
      return
    }

    if (action === 'read') {
      markAsRead(selectedNotifications)
    } else if (action === 'delete') {
      Modal.confirm({
        title: '确认删除',
        content: `确定要删除选中的 ${selectedNotifications.length} 条通知吗？`,
        onOk: () => {
          console.log('批量删除:', selectedNotifications)
          setSelectedNotifications([])
        }
      })
    }
  }

  // 更新通知设置
  const updateSetting = (id: string, field: string, value: boolean) => {
    console.log('更新设置:', { id, field, value })
  }

  // 发送自定义通知
  const handleSendNotification = (values: any) => {
    console.log('发送通知:', values)
    setIsComposeModalVisible(false)
    form.resetFields()
  }

  // 刷新数据
  const handleRefresh = () => {
    setLoading(true)
    setTimeout(() => {
      setLoading(false)
    }, 1000)
  }

  return (
    <div className="space-y-6">
      {/* 页面标题和操作 */}
      <div className="flex justify-between items-center">
        <div>
          <Title level={2} className="!mb-2">通知中心</Title>
          <Text className="text-gray-500">管理系统通知和消息设置</Text>
        </div>
        <Space>
          <Button 
            type="primary" 
            icon={<MessageOutlined />}
            onClick={() => setIsComposeModalVisible(true)}
          >
            发送通知
          </Button>
          <Button 
            icon={<SettingOutlined />}
            onClick={() => setIsSettingsModalVisible(true)}
          >
            通知设置
          </Button>
          <Button 
            icon={<ReloadOutlined />} 
            loading={loading}
            onClick={handleRefresh}
          >
            刷新
          </Button>
        </Space>
      </div>

      {/* 通知统计 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={6}>
          <Card className="dashboard-card">
            <Statistic
              title="总通知数"
              value={notificationStats.total}
              prefix={<BellOutlined className="text-blue-600" />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card className="dashboard-card">
            <Statistic
              title="未读通知"
              value={notificationStats.unread}
              prefix={<MailOutlined className="text-red-600" />}
              valueStyle={{ color: '#ef4444' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card className="dashboard-card">
            <Statistic
              title="今日通知"
              value={notificationStats.today}
              prefix={<MessageOutlined className="text-green-600" />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card className="dashboard-card">
            <Statistic
              title="本周通知"
              value={notificationStats.thisWeek}
              prefix={<SoundOutlined className="text-purple-600" />}
            />
          </Card>
        </Col>
      </Row>

      {/* 主要内容区域 */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane 
            tab={(
              <Badge count={notificationStats.unread} size="small">
                <span>通知列表</span>
              </Badge>
            )} 
            key="notifications"
          >
            {/* 筛选和批量操作 */}
            <div className="mb-4 flex justify-between items-center">
              <Space>
                <Select 
                  value={selectedType} 
                  onChange={setSelectedType}
                  style={{ width: 120 }}
                >
                  <Option value="all">全部</Option>
                  <Option value="unread">未读</Option>
                  <Option value="system">系统</Option>
                  <Option value="trading">交易</Option>
                  <Option value="risk">风险</Option>
                  <Option value="strategy">策略</Option>
                  <Option value="market">市场</Option>
                </Select>
                <Input.Search
                  placeholder="搜索通知内容"
                  style={{ width: 200 }}
                />
              </Space>
              <Space>
                <Button 
                  onClick={() => handleBatchAction('read')}
                  disabled={selectedNotifications.length === 0}
                >
                  标记已读
                </Button>
                <Button 
                  danger
                  onClick={() => handleBatchAction('delete')}
                  disabled={selectedNotifications.length === 0}
                >
                  批量删除
                </Button>
              </Space>
            </div>

            {/* 通知表格 */}
            <Table
              columns={notificationColumns}
              dataSource={filteredNotifications}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              className="data-table"
              scroll={{ x: 1000 }}
              rowSelection={{
                selectedRowKeys: selectedNotifications,
                onChange: (selectedRowKeys: React.Key[]) => setSelectedNotifications(selectedRowKeys as string[])
              }}
            />
          </TabPane>
          
          <TabPane tab="通知设置" key="settings">
            <div className="mb-4">
              <Alert
                message="通知设置说明"
                description="您可以根据需要开启或关闭不同类型的通知方式。建议保持重要通知（如风险预警）的多种通知方式开启。"
                type="info"
                showIcon
                closable
              />
            </div>
            
            <Table
              columns={settingsColumns}
              dataSource={notificationSettings}
              rowKey="id"
              pagination={false}
              className="data-table"
              scroll={{ x: 800 }}
            />
          </TabPane>
        </Tabs>
      </Card>

      {/* 通知设置模态框 */}
      <Modal
        title="全局通知设置"
        open={isSettingsModalVisible}
        onCancel={() => setIsSettingsModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setIsSettingsModalVisible(false)}>
            取消
          </Button>,
          <Button key="save" type="primary" onClick={() => setIsSettingsModalVisible(false)}>
            保存设置
          </Button>
        ]}
        width={600}
      >
        <div className="space-y-6">
          {/* 通知方式设置 */}
          <div>
            <Title level={4}>通知方式</Title>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <MailOutlined />
                  <span>邮件通知</span>
                </div>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <MobileOutlined />
                  <span>手机推送</span>
                </div>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <MessageOutlined />
                  <span>短信通知</span>
                </div>
                <Switch />
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <DesktopOutlined />
                  <span>桌面通知</span>
                </div>
                <Switch defaultChecked />
              </div>
            </div>
          </div>

          <Divider />

          {/* 免打扰时间 */}
          <div>
            <Title level={4}>免打扰时间</Title>
            <div className="space-y-3">
              <div className="flex items-center space-x-4">
                <Checkbox>启用免打扰模式</Checkbox>
              </div>
              <div className="flex items-center space-x-4">
                <span>从</span>
                <TimePicker defaultValue={dayjs('22:00', 'HH:mm')} format="HH:mm" />
                <span>到</span>
                <TimePicker defaultValue={dayjs('08:00', 'HH:mm')} format="HH:mm" />
              </div>
            </div>
          </div>

          <Divider />

          {/* 通知频率限制 */}
          <div>
            <Title level={4}>通知频率限制</Title>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span>每小时最大通知数</span>
                <InputNumber min={1} max={100} defaultValue={10} />
              </div>
              <div className="flex items-center justify-between">
                <span>相同类型通知间隔（分钟）</span>
                <InputNumber min={1} max={60} defaultValue={5} />
              </div>
            </div>
          </div>
        </div>
      </Modal>

      {/* 发送通知模态框 */}
      <Modal
        title="发送自定义通知"
        open={isComposeModalVisible}
        onCancel={() => {
          setIsComposeModalVisible(false)
          form.resetFields()
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSendNotification}
        >
          <Form.Item
            name="type"
            label="通知类型"
            rules={[{ required: true, message: '请选择通知类型' }]}
          >
            <Select placeholder="请选择通知类型">
              <Option value="system">系统通知</Option>
              <Option value="trading">交易通知</Option>
              <Option value="risk">风险通知</Option>
              <Option value="strategy">策略通知</Option>
              <Option value="market">市场通知</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="level"
            label="通知级别"
            rules={[{ required: true, message: '请选择通知级别' }]}
          >
            <Select placeholder="请选择通知级别">
              <Option value="info">信息</Option>
              <Option value="success">成功</Option>
              <Option value="warning">警告</Option>
              <Option value="error">错误</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="title"
            label="通知标题"
            rules={[{ required: true, message: '请输入通知标题' }]}
          >
            <Input placeholder="请输入通知标题" />
          </Form.Item>
          
          <Form.Item
            name="content"
            label="通知内容"
            rules={[{ required: true, message: '请输入通知内容' }]}
          >
            <TextArea 
              rows={4} 
              placeholder="请输入通知内容" 
              showCount 
              maxLength={500}
            />
          </Form.Item>
          
          <Form.Item
            name="channels"
            label="发送方式"
            rules={[{ required: true, message: '请选择发送方式' }]}
          >
            <Checkbox.Group>
              <Space direction="vertical">
                <Checkbox value="inApp">应用内通知</Checkbox>
                <Checkbox value="email">邮件通知</Checkbox>
                <Checkbox value="push">推送通知</Checkbox>
                <Checkbox value="sms">短信通知</Checkbox>
              </Space>
            </Checkbox.Group>
          </Form.Item>
          
          <Form.Item className="mb-0 text-right">
            <Space>
              <Button onClick={() => {
                setIsComposeModalVisible(false)
                form.resetFields()
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                发送通知
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default NotificationCenter