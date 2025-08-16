import React, { useState } from 'react'
import {
  Card, Table, Button, Space, Tag, Typography, Row, Col, Statistic,
  Select, Input, Modal, Form, InputNumber, Alert, Progress, Switch,
  Tooltip, Badge, Divider
} from 'antd'
import {
  WarningOutlined, ExclamationCircleOutlined,
  SettingOutlined, ReloadOutlined, BellOutlined, EyeOutlined,
  DollarOutlined, CheckOutlined, ArrowUpOutlined, ArrowDownOutlined
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { Option } = Select

interface RiskMetric {
  id: string
  name: string
  value: number
  threshold: number
  status: 'safe' | 'warning' | 'danger'
  description: string
  unit: string
}

interface RiskAlert {
  id: string
  type: 'position' | 'portfolio' | 'market' | 'system'
  level: 'low' | 'medium' | 'high' | 'critical'
  title: string
  description: string
  strategy?: string
  symbol?: string
  createdAt: string
  isRead: boolean
}

interface RiskLimit {
  id: string
  name: string
  type: 'position' | 'portfolio' | 'daily' | 'strategy'
  currentValue: number
  limitValue: number
  unit: string
  isEnabled: boolean
}

interface PortfolioRisk {
  totalValue: number
  totalRisk: number
  maxDrawdown: number
  sharpeRatio: number
  var95: number
  beta: number
  correlation: number
}

const RiskManagement: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [isLimitModalVisible, setIsLimitModalVisible] = useState(false)
  const [selectedAlert, setSelectedAlert] = useState<RiskAlert | null>(null)
  const [form] = Form.useForm()

  // 模拟数据
  const [portfolioRisk] = useState<PortfolioRisk>({
    totalValue: 125800,
    totalRisk: 15.6,
    maxDrawdown: -8.5,
    sharpeRatio: 1.85,
    var95: -2580,
    beta: 1.12,
    correlation: 0.78
  })

  const [riskMetrics] = useState<RiskMetric[]>([
    {
      id: '1',
      name: '保证金使用率',
      value: 32.5,
      threshold: 80,
      status: 'safe',
      description: '当前保证金使用率处于安全范围',
      unit: '%'
    },
    {
      id: '2',
      name: '最大回撤',
      value: 8.5,
      threshold: 15,
      status: 'safe',
      description: '最大回撤控制在合理范围内',
      unit: '%'
    },
    {
      id: '3',
      name: '集中度风险',
      value: 45.2,
      threshold: 50,
      status: 'warning',
      description: '单一资产占比较高，建议分散投资',
      unit: '%'
    },
    {
      id: '4',
      name: '波动率',
      value: 18.7,
      threshold: 25,
      status: 'safe',
      description: '投资组合波动率在可接受范围内',
      unit: '%'
    },
    {
      id: '5',
      name: '杠杆倍数',
      value: 2.8,
      threshold: 5,
      status: 'safe',
      description: '杠杆使用适中，风险可控',
      unit: 'x'
    },
    {
      id: '6',
      name: '流动性风险',
      value: 12.3,
      threshold: 20,
      status: 'safe',
      description: '流动性充足，可及时调整仓位',
      unit: '%'
    }
  ])

  const [riskAlerts] = useState<RiskAlert[]>([
    {
      id: '1',
      type: 'position',
      level: 'high',
      title: 'BTC/USDT持仓风险预警',
      description: '该持仓未实现亏损已达到-5.2%，接近止损线',
      strategy: '趋势跟踪策略A',
      symbol: 'BTC/USDT',
      createdAt: '2024-12-19 14:30:00',
      isRead: false
    },
    {
      id: '2',
      type: 'portfolio',
      level: 'medium',
      title: '投资组合集中度过高',
      description: 'BTC相关资产占比达到45.2%，建议适当分散',
      createdAt: '2024-12-19 13:45:00',
      isRead: false
    },
    {
      id: '3',
      type: 'market',
      level: 'medium',
      title: '市场波动率上升',
      description: '市场VIX指数上升至28.5，建议降低仓位',
      createdAt: '2024-12-19 12:20:00',
      isRead: true
    },
    {
      id: '4',
      type: 'system',
      level: 'low',
      title: '策略表现异常',
      description: '均值回归策略B连续3天表现不佳，建议检查参数',
      strategy: '均值回归策略B',
      createdAt: '2024-12-19 10:15:00',
      isRead: true
    }
  ])

  const [riskLimits] = useState<RiskLimit[]>([
    {
      id: '1',
      name: '单笔最大损失',
      type: 'position',
      currentValue: 2.5,
      limitValue: 5.0,
      unit: '%',
      isEnabled: true
    },
    {
      id: '2',
      name: '日最大损失',
      type: 'daily',
      currentValue: 1.8,
      limitValue: 3.0,
      unit: '%',
      isEnabled: true
    },
    {
      id: '3',
      name: '投资组合最大回撤',
      type: 'portfolio',
      currentValue: 8.5,
      limitValue: 15.0,
      unit: '%',
      isEnabled: true
    },
    {
      id: '4',
      name: '保证金使用率',
      type: 'portfolio',
      currentValue: 32.5,
      limitValue: 80.0,
      unit: '%',
      isEnabled: true
    },
    {
      id: '5',
      name: '单策略最大仓位',
      type: 'strategy',
      currentValue: 25.0,
      limitValue: 30.0,
      unit: '%',
      isEnabled: true
    }
  ])

  // 风险指标表格列配置
  const riskMetricColumns = [
    {
      title: '风险指标',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: '当前值',
      key: 'currentValue',
      render: (_: any, record: RiskMetric) => (
        <div className="flex items-center space-x-2">
          <Text>{record.value.toFixed(1)}{record.unit}</Text>
          <Progress
            percent={(record.value / record.threshold) * 100}
            size="small"
            strokeColor={
              record.status === 'safe' ? '#22c55e' :
              record.status === 'warning' ? '#f59e0b' : '#ef4444'
            }
            showInfo={false}
            style={{ width: 60 }}
          />
        </div>
      )
    },
    {
      title: '阈值',
      dataIndex: 'threshold',
      key: 'threshold',
      render: (value: number, record: RiskMetric) => `${value}${record.unit}`
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig = {
          safe: { color: 'green', text: '安全', icon: <CheckOutlined /> },
          warning: { color: 'orange', text: '警告', icon: <WarningOutlined /> },
          danger: { color: 'red', text: '危险', icon: <ExclamationCircleOutlined /> }
        }
        const config = statusConfig[status as keyof typeof statusConfig]
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        )
      }
    },
    {
      title: '说明',
      dataIndex: 'description',
      key: 'description'
    }
  ]

  // 风险预警表格列配置
  const alertColumns = [
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const typeConfig = {
          position: { color: 'blue', text: '持仓' },
          portfolio: { color: 'purple', text: '组合' },
          market: { color: 'orange', text: '市场' },
          system: { color: 'green', text: '系统' }
        }
        const config = typeConfig[type as keyof typeof typeConfig]
        return <Tag color={config.color}>{config.text}</Tag>
      }
    },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      render: (level: string) => {
        const levelConfig = {
          low: { color: 'green', text: '低' },
          medium: { color: 'orange', text: '中' },
          high: { color: 'red', text: '高' },
          critical: { color: 'red', text: '严重' }
        }
        const config = levelConfig[level as keyof typeof levelConfig]
        return <Tag color={config.color}>{config.text}</Tag>
      }
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      render: (text: string, record: RiskAlert) => (
        <div className="flex items-center space-x-2">
          {!record.isRead && <Badge status="processing" />}
          <Text strong={!record.isRead}>{text}</Text>
        </div>
      )
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description'
    },
    {
      title: '相关策略/交易对',
      key: 'related',
      render: (_: any, record: RiskAlert) => (
        <div>
          {record.strategy && <Tag color="blue">{record.strategy}</Tag>}
          {record.symbol && <Tag color="green">{record.symbol}</Tag>}
        </div>
      )
    },
    {
      title: '时间',
      dataIndex: 'createdAt',
      key: 'createdAt'
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: RiskAlert) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => setSelectedAlert(record)}
            />
          </Tooltip>
          {!record.isRead && (
            <Button
              type="link"
              size="small"
              onClick={() => markAsRead(record.id)}
            >
              标记已读
            </Button>
          )}
        </Space>
      )
    }
  ]

  // 风险限制表格列配置
  const limitColumns = [
    {
      title: '限制名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const typeConfig = {
          position: { color: 'blue', text: '持仓' },
          portfolio: { color: 'purple', text: '组合' },
          daily: { color: 'orange', text: '日限' },
          strategy: { color: 'green', text: '策略' }
        }
        const config = typeConfig[type as keyof typeof typeConfig]
        return <Tag color={config.color}>{config.text}</Tag>
      }
    },
    {
      title: '当前值/限制值',
      key: 'values',
      render: (_: any, record: RiskLimit) => (
        <div>
          <div className="flex items-center space-x-2">
            <Text>{record.currentValue.toFixed(1)}{record.unit}</Text>
            <Text className="text-gray-400">/</Text>
            <Text>{record.limitValue.toFixed(1)}{record.unit}</Text>
          </div>
          <Progress
            percent={(record.currentValue / record.limitValue) * 100}
            size="small"
            strokeColor={
              (record.currentValue / record.limitValue) > 0.8 ? '#ef4444' :
              (record.currentValue / record.limitValue) > 0.6 ? '#f59e0b' : '#22c55e'
            }
            showInfo={false}
            className="mt-1"
          />
        </div>
      )
    },
    {
      title: '状态',
      dataIndex: 'isEnabled',
      key: 'isEnabled',
      render: (isEnabled: boolean) => (
        <Switch
          checked={isEnabled}
          size="small"
          onChange={(checked) => toggleLimit(checked)}
        />
      )
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: RiskLimit) => (
        <Button
          type="link"
          size="small"
          onClick={() => editLimit(record)}
        >
          编辑
        </Button>
      )
    }
  ]

  // 风险分布图配置
  const riskDistributionOption = {
    title: {
      text: '风险分布',
      left: 'center'
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c}% ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '风险类型',
        type: 'pie',
        radius: '50%',
        data: [
          { value: 35, name: '市场风险' },
          { value: 25, name: '信用风险' },
          { value: 20, name: '流动性风险' },
          { value: 15, name: '操作风险' },
          { value: 5, name: '其他风险' }
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }

  // VaR历史图配置
  const varHistoryOption = {
    title: {
      text: 'VaR历史走势',
      left: 'left'
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const data = params[0]
        return `${data.name}<br/>VaR: $${Math.abs(data.value).toFixed(0)}`
      }
    },
    xAxis: {
      type: 'category',
      data: Array.from({ length: 30 }, (_, i) => 
        dayjs().subtract(29 - i, 'day').format('MM-DD')
      )
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '${value}'
      }
    },
    series: [{
      data: Array.from({ length: 30 }, () => -(Math.random() * 3000 + 1000)),
      type: 'line',
      smooth: true,
      lineStyle: { color: '#ef4444', width: 2 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(239, 68, 68, 0.3)' },
            { offset: 1, color: 'rgba(239, 68, 68, 0.05)' }
          ]
        }
      }
    }]
  }

  // 标记已读
  const markAsRead = (alertId: string) => {
    console.log('标记已读:', alertId)
  }

  // 切换限制状态
  const toggleLimit = (checked: boolean) => {
    console.log('切换限制状态:', checked)
  }

  // 编辑限制
  const editLimit = (limit: RiskLimit) => {
    form.setFieldsValue(limit)
    setIsLimitModalVisible(true)
  }

  // 保存限制设置
  const handleSaveLimit = (values: any) => {
    console.log('保存限制设置:', values)
    setIsLimitModalVisible(false)
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
          <Title level={2} className="!mb-2">风险管理</Title>
          <Text className="text-gray-500">实时监控和管理投资组合风险</Text>
        </div>
        <Space>
          <Button 
            type="primary" 
            icon={<SettingOutlined />}
            onClick={() => setIsLimitModalVisible(true)}
          >
            风险设置
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

      {/* 风险概览 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="投资组合风险"
              value={portfolioRisk.totalRisk}
              precision={1}
              prefix={<CheckOutlined className="text-orange-500" />}
              suffix="%"
              valueStyle={{ color: portfolioRisk.totalRisk > 20 ? '#ef4444' : '#22c55e' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="最大回撤"
              value={Math.abs(portfolioRisk.maxDrawdown)}
              precision={1}
              prefix={<ArrowDownOutlined className="text-red-600" />}
              suffix="%"
              valueStyle={{ color: '#ef4444' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="夏普比率"
              value={portfolioRisk.sharpeRatio}
              precision={2}
              prefix={<ArrowUpOutlined className="text-green-600" />}
              valueStyle={{ color: portfolioRisk.sharpeRatio > 1 ? '#22c55e' : '#ef4444' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="VaR (95%)"
              value={Math.abs(portfolioRisk.var95)}
              prefix={<DollarOutlined className="text-purple-600" />}
              suffix="USD"
              valueStyle={{ color: '#8b5cf6' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 风险预警 */}
      <Card 
        title={(
          <div className="flex items-center space-x-2">
            <BellOutlined />
            <span>风险预警</span>
            <Badge 
              count={riskAlerts.filter(alert => !alert.isRead).length} 
              size="small"
            />
          </div>
        )}
        className="dashboard-card"
      >
        {riskAlerts.filter(alert => !alert.isRead).length > 0 && (
          <Alert
            message="您有未读的风险预警"
            description={`共有 ${riskAlerts.filter(alert => !alert.isRead).length} 条未读预警，请及时处理。`}
            type="warning"
            showIcon
            closable
            className="mb-4"
          />
        )}
        <Table
          columns={alertColumns}
          dataSource={riskAlerts}
          rowKey="id"
          pagination={{ pageSize: 5 }}
          className="data-table"
          scroll={{ x: 1000 }}
        />
      </Card>

      {/* 主要内容区域 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card title="风险指标监控" className="dashboard-card">
            <Table
              columns={riskMetricColumns}
              dataSource={riskMetrics}
              rowKey="id"
              pagination={false}
              className="data-table"
            />
          </Card>
        </Col>
        
        <Col xs={24} lg={8}>
          <div className="space-y-4">
            {/* 风险分布 */}
            <Card title="风险分布" className="dashboard-card">
              <ReactECharts 
                option={riskDistributionOption} 
                style={{ height: '250px' }} 
              />
            </Card>
            
            {/* 投资组合指标 */}
            <Card title="投资组合指标" className="dashboard-card">
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <Text>Beta系数</Text>
                  <Text strong>{portfolioRisk.beta.toFixed(2)}</Text>
                </div>
                <div className="flex justify-between items-center">
                  <Text>相关性</Text>
                  <Text strong>{portfolioRisk.correlation.toFixed(2)}</Text>
                </div>
                <Divider className="my-3" />
                <div>
                  <Text className="text-gray-500">风险等级</Text>
                  <div className="mt-2">
                    <Progress
                      percent={portfolioRisk.totalRisk * 4}
                      strokeColor={
                        portfolioRisk.totalRisk < 10 ? '#22c55e' :
                        portfolioRisk.totalRisk < 20 ? '#f59e0b' : '#ef4444'
                      }
                      format={() => 
                        portfolioRisk.totalRisk < 10 ? '低风险' :
                        portfolioRisk.totalRisk < 20 ? '中风险' : '高风险'
                      }
                    />
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </Col>
      </Row>

      {/* VaR历史走势 */}
      <Card title="VaR历史走势" className="dashboard-card">
        <ReactECharts option={varHistoryOption} style={{ height: '300px' }} />
      </Card>

      {/* 风险限制设置 */}
      <Card title="风险限制设置" className="dashboard-card">
        <Table
          columns={limitColumns}
          dataSource={riskLimits}
          rowKey="id"
          pagination={false}
          className="data-table"
        />
      </Card>

      {/* 风险限制设置模态框 */}
      <Modal
        title="风险限制设置"
        open={isLimitModalVisible}
        onCancel={() => {
          setIsLimitModalVisible(false)
          form.resetFields()
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveLimit}
        >
          <Form.Item
            name="name"
            label="限制名称"
            rules={[{ required: true, message: '请输入限制名称' }]}
          >
            <Input placeholder="请输入限制名称" />
          </Form.Item>
          
          <Form.Item
            name="type"
            label="限制类型"
            rules={[{ required: true, message: '请选择限制类型' }]}
          >
            <Select placeholder="请选择限制类型">
              <Option value="position">持仓限制</Option>
              <Option value="portfolio">组合限制</Option>
              <Option value="daily">日限制</Option>
              <Option value="strategy">策略限制</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="limitValue"
            label="限制值"
            rules={[{ required: true, message: '请输入限制值' }]}
          >
            <InputNumber
              style={{ width: '100%' }}
              placeholder="请输入限制值"
              min={0}
              step={0.1}
            />
          </Form.Item>
          
          <Form.Item
            name="unit"
            label="单位"
            rules={[{ required: true, message: '请选择单位' }]}
          >
            <Select placeholder="请选择单位">
              <Option value="%">百分比 (%)</Option>
              <Option value="USD">美元 (USD)</Option>
              <Option value="x">倍数 (x)</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="isEnabled"
            label="启用状态"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
          
          <Form.Item className="mb-0 text-right">
            <Space>
              <Button onClick={() => {
                setIsLimitModalVisible(false)
                form.resetFields()
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                保存
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 预警详情模态框 */}
      {selectedAlert && (
        <Modal
          title="预警详情"
          open={!!selectedAlert}
          onCancel={() => setSelectedAlert(null)}
          footer={[
            <Button key="close" onClick={() => setSelectedAlert(null)}>
              关闭
            </Button>,
            !selectedAlert.isRead && (
              <Button key="markRead" type="primary" onClick={() => {
                markAsRead(selectedAlert.id)
                setSelectedAlert(null)
              }}>
                标记已读
              </Button>
            )
          ]}
        >
          <div className="space-y-4">
            <div>
              <Text strong>预警类型：</Text>
              <Tag color="blue" className="ml-2">{selectedAlert.type}</Tag>
            </div>
            <div>
              <Text strong>预警级别：</Text>
              <Tag 
                color={
                  selectedAlert.level === 'critical' ? 'red' :
                  selectedAlert.level === 'high' ? 'red' :
                  selectedAlert.level === 'medium' ? 'orange' : 'green'
                } 
                className="ml-2"
              >
                {selectedAlert.level}
              </Tag>
            </div>
            <div>
              <Text strong>标题：</Text>
              <br />
              <Text>{selectedAlert.title}</Text>
            </div>
            <div>
              <Text strong>详细描述：</Text>
              <br />
              <Text>{selectedAlert.description}</Text>
            </div>
            {selectedAlert.strategy && (
              <div>
                <Text strong>相关策略：</Text>
                <br />
                <Tag color="blue">{selectedAlert.strategy}</Tag>
              </div>
            )}
            {selectedAlert.symbol && (
              <div>
                <Text strong>相关交易对：</Text>
                <br />
                <Tag color="green">{selectedAlert.symbol}</Tag>
              </div>
            )}
            <div>
              <Text strong>创建时间：</Text>
              <br />
              <Text>{selectedAlert.createdAt}</Text>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}

export default RiskManagement