import React, { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, Progress, Table, Tag, Space, Typography, Button, Alert } from 'antd'
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  DollarOutlined,
  TrophyOutlined,
  RocketOutlined,
  ShieldCheckOutlined,
  ReloadOutlined,
  EyeOutlined
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'

const { Title, Text } = Typography

interface PortfolioData {
  totalValue: number
  todayPnL: number
  todayPnLPercent: number
  totalPnL: number
  totalPnLPercent: number
  availableBalance: number
  marginUsed: number
  marginRatio: number
}

interface StrategyData {
  id: string
  name: string
  status: 'running' | 'stopped' | 'error'
  todayPnL: number
  totalPnL: number
  winRate: number
  sharpeRatio: number
}

interface MarketData {
  symbol: string
  price: number
  change: number
  changePercent: number
  volume: string
}

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [portfolioData, setPortfolioData] = useState<PortfolioData>({
    totalValue: 125680.50,
    todayPnL: 2340.80,
    todayPnLPercent: 1.89,
    totalPnL: 25680.50,
    totalPnLPercent: 25.68,
    availableBalance: 85420.30,
    marginUsed: 40260.20,
    marginRatio: 32.05
  })

  const [strategies] = useState<StrategyData[]>([
    {
      id: '1',
      name: '趋势跟踪策略A',
      status: 'running',
      todayPnL: 1250.30,
      totalPnL: 8960.50,
      winRate: 68.5,
      sharpeRatio: 1.85
    },
    {
      id: '2', 
      name: '均值回归策略B',
      status: 'running',
      todayPnL: 890.20,
      totalPnL: 12340.80,
      winRate: 72.3,
      sharpeRatio: 2.12
    },
    {
      id: '3',
      name: '套利策略C',
      status: 'stopped',
      todayPnL: 200.30,
      totalPnL: 4379.20,
      winRate: 85.2,
      sharpeRatio: 1.67
    }
  ])

  const [marketData] = useState<MarketData[]>([
    { symbol: 'BTC/USDT', price: 43250.80, change: 1250.30, changePercent: 2.98, volume: '2.5B' },
    { symbol: 'ETH/USDT', price: 2680.45, change: -45.20, changePercent: -1.66, volume: '1.8B' },
    { symbol: 'BNB/USDT', price: 315.60, change: 8.90, changePercent: 2.90, volume: '450M' },
    { symbol: 'SOL/USDT', price: 98.75, change: 3.25, changePercent: 3.40, volume: '680M' }
  ])

  // 收益曲线图表配置
  const pnlChartOption = {
    title: {
      text: '收益曲线',
      left: 'left',
      textStyle: { fontSize: 16, fontWeight: 'bold' }
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const data = params[0]
        return `${data.name}<br/>累计收益: $${data.value.toLocaleString()}`
      }
    },
    xAxis: {
      type: 'category',
      data: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '${value}'
      }
    },
    series: [{
      data: [100000, 102500, 105800, 103200, 108900, 112400, 115600, 118900, 121200, 119800, 123400, 125680],
      type: 'line',
      smooth: true,
      lineStyle: { color: '#1890ff', width: 3 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
            { offset: 1, color: 'rgba(24, 144, 255, 0.05)' }
          ]
        }
      }
    }]
  }

  // 策略表格列配置
  const strategyColumns = [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: StrategyData) => (
        <Space>
          <div className={`status-indicator status-${record.status}`}></div>
          <Text strong>{text}</Text>
        </Space>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusMap = {
          running: { color: 'green', text: '运行中' },
          stopped: { color: 'red', text: '已停止' },
          error: { color: 'orange', text: '异常' }
        }
        const config = statusMap[status as keyof typeof statusMap]
        return <Tag color={config.color}>{config.text}</Tag>
      }
    },
    {
      title: '今日盈亏',
      dataIndex: 'todayPnL',
      key: 'todayPnL',
      render: (value: number) => (
        <Text className={value >= 0 ? 'text-green-600' : 'text-red-600'}>
          ${value.toFixed(2)}
        </Text>
      )
    },
    {
      title: '累计盈亏',
      dataIndex: 'totalPnL',
      key: 'totalPnL',
      render: (value: number) => (
        <Text className={value >= 0 ? 'text-green-600' : 'text-red-600'}>
          ${value.toFixed(2)}
        </Text>
      )
    },
    {
      title: '胜率',
      dataIndex: 'winRate',
      key: 'winRate',
      render: (value: number) => `${value}%`
    },
    {
      title: '夏普比率',
      dataIndex: 'sharpeRatio',
      key: 'sharpeRatio',
      render: (value: number) => value.toFixed(2)
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record: StrategyData) => (
        <Space>
          <Button type="link" size="small" icon={<EyeOutlined />}>
            查看
          </Button>
        </Space>
      )
    }
  ]

  // 市场数据表格列配置
  const marketColumns = [
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (value: number) => `$${value.toLocaleString()}`
    },
    {
      title: '24h变化',
      key: 'change',
      render: (_, record: MarketData) => (
        <Space>
          <Text className={record.change >= 0 ? 'text-green-600' : 'text-red-600'}>
            {record.change >= 0 ? '+' : ''}${record.change.toFixed(2)}
          </Text>
          <Text className={record.changePercent >= 0 ? 'text-green-600' : 'text-red-600'}>
            ({record.changePercent >= 0 ? '+' : ''}{record.changePercent.toFixed(2)}%)
          </Text>
        </Space>
      )
    },
    {
      title: '24h成交量',
      dataIndex: 'volume',
      key: 'volume'
    }
  ]

  const handleRefresh = () => {
    setLoading(true)
    // 模拟数据刷新
    setTimeout(() => {
      setLoading(false)
    }, 1000)
  }

  return (
    <div className="space-y-6">
      {/* 页面标题和操作 */}
      <div className="flex justify-between items-center">
        <div>
          <Title level={2} className="!mb-2">仪表板</Title>
          <Text className="text-gray-500">实时监控您的交易组合和策略表现</Text>
        </div>
        <Button 
          type="primary" 
          icon={<ReloadOutlined />} 
          loading={loading}
          onClick={handleRefresh}
        >
          刷新数据
        </Button>
      </div>

      {/* 系统状态提醒 */}
      <Alert
        message="系统运行正常"
        description="所有服务运行正常，数据更新及时。最后更新时间：2024-12-19 14:30:25"
        type="success"
        showIcon
        closable
      />

      {/* 核心指标卡片 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="总资产价值"
              value={portfolioData.totalValue}
              precision={2}
              prefix={<DollarOutlined className="text-blue-600" />}
              suffix="USD"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="今日盈亏"
              value={portfolioData.todayPnL}
              precision={2}
              prefix={portfolioData.todayPnL >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              suffix={`USD (${portfolioData.todayPnLPercent >= 0 ? '+' : ''}${portfolioData.todayPnLPercent}%)`}
              valueStyle={{ color: portfolioData.todayPnL >= 0 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="累计盈亏"
              value={portfolioData.totalPnL}
              precision={2}
              prefix={<TrophyOutlined className="text-orange-500" />}
              suffix={`USD (${portfolioData.totalPnLPercent >= 0 ? '+' : ''}${portfolioData.totalPnLPercent}%)`}
              valueStyle={{ color: portfolioData.totalPnL >= 0 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="保证金使用率"
              value={portfolioData.marginRatio}
              precision={2}
              prefix={<ShieldCheckOutlined className="text-purple-600" />}
              suffix="%"
              valueStyle={{ color: portfolioData.marginRatio > 80 ? '#cf1322' : '#1890ff' }}
            />
            <Progress 
              percent={portfolioData.marginRatio} 
              showInfo={false} 
              strokeColor={portfolioData.marginRatio > 80 ? '#ff4d4f' : '#1890ff'}
              className="mt-2"
            />
          </Card>
        </Col>
      </Row>

      {/* 图表和数据 */}
      <Row gutter={[16, 16]}>
        {/* 收益曲线图 */}
        <Col xs={24} lg={16}>
          <Card title="收益曲线" className="dashboard-card">
            <ReactECharts option={pnlChartOption} style={{ height: '400px' }} />
          </Card>
        </Col>

        {/* 资产分布 */}
        <Col xs={24} lg={8}>
          <Card title="资产分布" className="dashboard-card">
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <Text>可用余额</Text>
                <Text strong>${portfolioData.availableBalance.toLocaleString()}</Text>
              </div>
              <Progress 
                percent={(portfolioData.availableBalance / portfolioData.totalValue) * 100} 
                strokeColor="#52c41a"
                format={() => `${((portfolioData.availableBalance / portfolioData.totalValue) * 100).toFixed(1)}%`}
              />
              
              <div className="flex justify-between items-center">
                <Text>已用保证金</Text>
                <Text strong>${portfolioData.marginUsed.toLocaleString()}</Text>
              </div>
              <Progress 
                percent={(portfolioData.marginUsed / portfolioData.totalValue) * 100} 
                strokeColor="#faad14"
                format={() => `${((portfolioData.marginUsed / portfolioData.totalValue) * 100).toFixed(1)}%`}
              />

              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <Text className="text-sm text-gray-600">风险提示</Text>
                <div className="mt-2">
                  <Text className="text-sm">
                    当前保证金使用率为 {portfolioData.marginRatio}%
                    {portfolioData.marginRatio > 80 && (
                      <span className="text-red-500 ml-1">（风险较高）</span>
                    )}
                  </Text>
                </div>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 策略表现 */}
      <Card 
        title={(
          <Space>
            <RocketOutlined />
            <span>策略表现</span>
          </Space>
        )} 
        className="dashboard-card"
      >
        <Table
          columns={strategyColumns}
          dataSource={strategies}
          rowKey="id"
          pagination={false}
          size="middle"
          className="data-table"
        />
      </Card>

      {/* 市场行情 */}
      <Card title="市场行情" className="dashboard-card">
        <Table
          columns={marketColumns}
          dataSource={marketData}
          rowKey="symbol"
          pagination={false}
          size="middle"
          className="data-table"
        />
      </Card>
    </div>
  )
}

export default Dashboard