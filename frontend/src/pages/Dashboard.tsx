import React, { useEffect, useState } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Button,
  Space,
  Typography,
  Progress,
  Alert,
  Spin
} from 'antd'
import {
  DollarOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  TrophyOutlined,
  SafetyOutlined,
  RocketOutlined,
  ReloadOutlined
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import {
  useTradingStore,
  useStrategyStore,
  useMarketStore,
  useRiskStore,
  useNotificationStore
} from '../store'

const { Title, Text } = Typography

interface PortfolioData {
  totalValue: number
  availableBalance: number
  marginUsed: number
  todayPnL: number
  todayPnLPercent: number
  totalPnL: number
  totalPnLPercent: number
  marginRatio: number
}

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(false)
  
  // Zustand stores
  const { balance, fetchBalance } = useTradingStore()
  const { strategies, fetchStrategies } = useStrategyStore()
  const { marketData, fetchMarketData } = useMarketStore()
  const { fetchRiskMetrics } = useRiskStore()
  const { fetchNotifications } = useNotificationStore()

  // 计算组合数据
  const portfolioData: PortfolioData = {
    totalValue: balance?.total || 0,
    availableBalance: balance?.available || 0,
    marginUsed: balance?.margin_used || 0,
    todayPnL: balance?.today_pnl || 0,
    todayPnLPercent: balance?.today_pnl_percent || 0,
    totalPnL: balance?.total_pnl || 0,
    totalPnLPercent: balance?.total_pnl_percent || 0,
    marginRatio: balance?.margin_ratio || 0
  }

  // 初始化数据加载
  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      try {
        await Promise.all([
          fetchBalance(),
          fetchStrategies(),
          fetchMarketData(),
          fetchRiskMetrics(),
          fetchNotifications()
        ])
      } catch (error) {
        console.error('Failed to load data:', error)
      } finally {
        setLoading(false)
      }
    }

    loadData()

    // 设置定时刷新
    const interval = setInterval(loadData, 30000) // 30秒刷新一次
    return () => clearInterval(interval)
  }, [])

  // 收益曲线图表配置
  const pnlChartOption = {
    title: {
      text: '收益曲线',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: '{b}: {c}%'
    },
    xAxis: {
      type: 'category',
      data: balance?.pnl_history?.map((item: any) => item.date) || []
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [{
      data: balance?.pnl_history?.map((item: any) => item.pnl_percent) || [],
      type: 'line',
      smooth: true,
      itemStyle: {
        color: '#1890ff'
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [{
            offset: 0, color: 'rgba(24, 144, 255, 0.3)'
          }, {
            offset: 1, color: 'rgba(24, 144, 255, 0.1)'
          }]
        }
      }
    }]
  }

  // 策略表格列配置
  const strategyColumns = [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name'
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <span className={`px-2 py-1 rounded text-xs ${
          status === 'running' ? 'bg-green-100 text-green-800' :
          status === 'stopped' ? 'bg-red-100 text-red-800' :
          'bg-yellow-100 text-yellow-800'
        }`}>
          {status === 'running' ? '运行中' : status === 'stopped' ? '已停止' : '暂停'}
        </span>
      )
    },
    {
      title: '今日收益',
      dataIndex: 'today_pnl',
      key: 'today_pnl',
      render: (value: number) => (
        <span className={value >= 0 ? 'text-green-600' : 'text-red-600'}>
          {value >= 0 ? '+' : ''}{value?.toFixed(2)}%
        </span>
      )
    },
    {
      title: '累计收益',
      dataIndex: 'total_pnl',
      key: 'total_pnl',
      render: (value: number) => (
        <span className={value >= 0 ? 'text-green-600' : 'text-red-600'}>
          {value >= 0 ? '+' : ''}{value?.toFixed(2)}%
        </span>
      )
    },
    {
      title: '操作',
      key: 'action',
      render: () => (
        <Space>
          <Button type="link" size="small">查看</Button>
          <Button type="link" size="small">编辑</Button>
        </Space>
      )
    }
  ]

  // 市场行情表格列配置
  const marketColumns = [
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol'
    },
    {
      title: '最新价格',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => `$${price?.toLocaleString()}`
    },
    {
      title: '24h涨跌',
      dataIndex: 'change_24h',
      key: 'change_24h',
      render: (value: number) => (
        <Space>
          {value >= 0 ? <ArrowUpOutlined className="text-green-600" /> : <ArrowDownOutlined className="text-red-600" />}
          <span className={value >= 0 ? 'text-green-600' : 'text-red-600'}>
            {value >= 0 ? '+' : ''}{value?.toFixed(2)}%
          </span>
        </Space>
      )
    },
    {
      title: '24h成交量',
      dataIndex: 'volume',
      key: 'volume'
    }
  ]

  const handleRefresh = async () => {
    setLoading(true)
    try {
      await Promise.all([
        fetchBalance(),
        fetchStrategies(),
        fetchMarketData(),
        fetchRiskMetrics()
      ])
    } catch (error) {
      console.error('Failed to refresh data:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Spin spinning={loading}>
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
                prefix={<SafetyOutlined className="text-purple-600" />}
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
            dataSource={strategies || []}
            rowKey="id"
            pagination={false}
            size="middle"
            className="data-table"
            loading={loading}
          />
        </Card>

        {/* 市场行情 */}
        <Card title="市场行情" className="dashboard-card">
          <Table
            columns={marketColumns}
            dataSource={marketData || []}
            rowKey="symbol"
            pagination={false}
            size="middle"
            className="data-table"
            loading={loading}
          />
        </Card>
      </div>
    </Spin>
  )
}

export default Dashboard