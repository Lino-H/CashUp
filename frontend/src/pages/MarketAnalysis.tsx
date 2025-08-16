import React, { useState, useEffect } from 'react'
import {
  Card, Table, Button, Space, Tag, Typography, Row, Col, Statistic,
  Select, Input, Tabs, Alert, Tooltip, Progress, Switch
} from 'antd'
import {
  LineChartOutlined, BarChartOutlined, PieChartOutlined, ReloadOutlined,
  SearchOutlined, FilterOutlined, StarOutlined, StarFilled,
  ArrowUpOutlined, ArrowDownOutlined, DollarOutlined,
  ThunderboltOutlined, EyeOutlined, SettingOutlined
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { Option } = Select
const { TabPane } = Tabs

interface MarketData {
  symbol: string
  price: number
  change24h: number
  changePercent24h: number
  volume24h: number
  marketCap: number
  high24h: number
  low24h: number
  isFavorite: boolean
}

interface TechnicalIndicator {
  name: string
  value: number
  signal: 'buy' | 'sell' | 'neutral'
  description: string
}

interface MarketStats {
  totalMarketCap: number
  totalVolume24h: number
  btcDominance: number
  fearGreedIndex: number
  activeCoins: number
  gainers: number
  losers: number
}

const MarketAnalysis: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedSymbol, setSelectedSymbol] = useState('BTC/USDT')
  const [timeframe, setTimeframe] = useState('1h')
  const [showVolume, setShowVolume] = useState(true)
  const [, setFavorites] = useState<string[]>(['BTC/USDT', 'ETH/USDT'])

  // 模拟数据
  const [marketStats] = useState<MarketStats>({
    totalMarketCap: 1680000000000,
    totalVolume24h: 89500000000,
    btcDominance: 52.3,
    fearGreedIndex: 68,
    activeCoins: 2847,
    gainers: 1256,
    losers: 1591
  })

  const [marketData] = useState<MarketData[]>([
    {
      symbol: 'BTC/USDT',
      price: 43250.50,
      change24h: 1250.30,
      changePercent24h: 2.98,
      volume24h: 28500000000,
      marketCap: 847000000000,
      high24h: 43800.00,
      low24h: 41900.00,
      isFavorite: true
    },
    {
      symbol: 'ETH/USDT',
      price: 2680.75,
      change24h: -45.25,
      changePercent24h: -1.66,
      volume24h: 15200000000,
      marketCap: 322000000000,
      high24h: 2750.00,
      low24h: 2650.00,
      isFavorite: true
    },
    {
      symbol: 'BNB/USDT',
      price: 315.60,
      change24h: 8.90,
      changePercent24h: 2.90,
      volume24h: 1850000000,
      marketCap: 47200000000,
      high24h: 320.00,
      low24h: 305.00,
      isFavorite: false
    },
    {
      symbol: 'SOL/USDT',
      price: 98.75,
      change24h: 5.25,
      changePercent24h: 5.61,
      volume24h: 2100000000,
      marketCap: 42800000000,
      high24h: 102.00,
      low24h: 92.50,
      isFavorite: false
    },
    {
      symbol: 'ADA/USDT',
      price: 0.485,
      change24h: -0.015,
      changePercent24h: -3.00,
      volume24h: 890000000,
      marketCap: 17200000000,
      high24h: 0.510,
      low24h: 0.475,
      isFavorite: false
    }
  ])

  const [technicalIndicators] = useState<TechnicalIndicator[]>([
    {
      name: 'RSI (14)',
      value: 68.5,
      signal: 'neutral',
      description: '相对强弱指数，当前处于中性区域'
    },
    {
      name: 'MACD',
      value: 125.8,
      signal: 'buy',
      description: 'MACD线在信号线上方，呈现买入信号'
    },
    {
      name: 'MA(20)',
      value: 42800,
      signal: 'buy',
      description: '价格在20日均线上方，趋势向上'
    },
    {
      name: 'Bollinger Bands',
      value: 0.75,
      signal: 'neutral',
      description: '价格在布林带中轨附近，波动性适中'
    },
    {
      name: 'Volume',
      value: 1.25,
      signal: 'buy',
      description: '成交量放大，支持价格上涨'
    }
  ])

  // K线图配置
  const candlestickOption = {
    title: {
      text: `${selectedSymbol} - ${timeframe}`,
      left: 'left'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: (params: any) => {
        const data = params[0]
        if (data && data.data) {
          const [open, close, low, high] = data.data.slice(1)
          return `
            时间: ${data.name}<br/>
            开盘: $${open.toFixed(2)}<br/>
            收盘: $${close.toFixed(2)}<br/>
            最高: $${high.toFixed(2)}<br/>
            最低: $${low.toFixed(2)}
          `
        }
        return ''
      }
    },
    legend: {
      data: ['K线', '成交量'],
      top: 30
    },
    grid: [
      {
        left: '10%',
        right: '8%',
        height: showVolume ? '50%' : '70%'
      },
      {
        left: '10%',
        right: '8%',
        top: '70%',
        height: '15%',
        show: showVolume
      }
    ],
    xAxis: [
      {
        type: 'category',
        data: Array.from({ length: 50 }, (_, i) => {
          const date = dayjs().subtract(49 - i, timeframe === '1h' ? 'hour' : 'day')
          return timeframe === '1h' ? date.format('HH:mm') : date.format('MM-DD')
        }),
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        splitLine: { show: false },
        min: 'dataMin',
        max: 'dataMax'
      },
      {
        type: 'category',
        gridIndex: 1,
        data: Array.from({ length: 50 }, (_, i) => {
          const date = dayjs().subtract(49 - i, timeframe === '1h' ? 'hour' : 'day')
          return timeframe === '1h' ? date.format('HH:mm') : date.format('MM-DD')
        }),
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        splitLine: { show: false },
        min: 'dataMin',
        max: 'dataMax',
        show: showVolume
      }
    ],
    yAxis: [
      {
        scale: true,
        splitArea: {
          show: true
        }
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
        show: showVolume
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: 80,
        end: 100
      },
      {
        show: true,
        xAxisIndex: [0, 1],
        type: 'slider',
        top: '85%',
        start: 80,
        end: 100
      }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: Array.from({ length: 50 }, () => {
          const base = 43000 + Math.random() * 1000
          const open = base + Math.random() * 200 - 100
          const close = open + Math.random() * 400 - 200
          const high = Math.max(open, close) + Math.random() * 100
          const low = Math.min(open, close) - Math.random() * 100
          return [open, close, low, high]
        }),
        itemStyle: {
          color: '#ef4444',
          color0: '#22c55e',
          borderColor: '#ef4444',
          borderColor0: '#22c55e'
        }
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: Array.from({ length: 50 }, () => Math.random() * 1000000),
        itemStyle: {
          color: '#64748b'
        },
        show: showVolume
      }
    ]
  }

  // 市场分布图配置
  const marketDistributionOption = {
    title: {
      text: '市场份额分布',
      left: 'center'
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: ${c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '市值',
        type: 'pie',
        radius: '50%',
        data: [
          { value: 847, name: 'Bitcoin' },
          { value: 322, name: 'Ethereum' },
          { value: 47, name: 'BNB' },
          { value: 43, name: 'Solana' },
          { value: 17, name: 'Cardano' },
          { value: 124, name: '其他' }
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

  // 恐慌贪婪指数图配置
  const fearGreedOption = {
    title: {
      text: '恐慌贪婪指数',
      left: 'center'
    },
    series: [
      {
        type: 'gauge',
        startAngle: 180,
        endAngle: 0,
        center: ['50%', '75%'],
        radius: '90%',
        min: 0,
        max: 100,
        splitNumber: 5,
        axisLine: {
          lineStyle: {
            width: 6,
            color: [
              [0.2, '#ef4444'],
              [0.4, '#f97316'],
              [0.6, '#eab308'],
              [0.8, '#84cc16'],
              [1, '#22c55e']
            ]
          }
        },
        pointer: {
          icon: 'path://M12.8,0.7l12,40.1H0.7L12.8,0.7z',
          length: '12%',
          width: 20,
          offsetCenter: [0, '-60%'],
          itemStyle: {
            color: 'auto'
          }
        },
        axisTick: {
          length: 12,
          lineStyle: {
            color: 'auto',
            width: 2
          }
        },
        splitLine: {
          length: 20,
          lineStyle: {
            color: 'auto',
            width: 5
          }
        },
        axisLabel: {
          color: '#464646',
          fontSize: 12,
          distance: -60,
          formatter: function (value: number) {
            if (value <= 20) return '极度恐慌'
            if (value <= 40) return '恐慌'
            if (value <= 60) return '中性'
            if (value <= 80) return '贪婪'
            return '极度贪婪'
          }
        },
        title: {
          offsetCenter: [0, '-20%'],
          fontSize: 16
        },
        detail: {
          fontSize: 24,
          offsetCenter: [0, '0%'],
          valueAnimation: true,
          formatter: function (value: number) {
            return Math.round(value) + ''
          },
          color: 'auto'
        },
        data: [
          {
            value: marketStats.fearGreedIndex,
            name: '当前指数'
          }
        ]
      }
    ]
  }

  // 市场数据表格列配置
  const marketColumns = [
    {
      title: '收藏',
      key: 'favorite',
      width: 60,
      render: (_: any, record: MarketData) => (
        <Button
          type="text"
          size="small"
          icon={record.isFavorite ? <StarFilled className="text-yellow-500" /> : <StarOutlined />}
          onClick={() => toggleFavorite(record.symbol)}
        />
      )
    },
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (text: string) => (
        <div className="flex items-center space-x-2">
          <Text strong>{text}</Text>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => setSelectedSymbol(text)}
          />
        </div>
      )
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (value: number) => `$${value.toLocaleString()}`
    },
    {
      title: '24h涨跌',
      key: 'change24h',
      render: (_: any, record: MarketData) => (
        <div>
          <Text className={record.change24h >= 0 ? 'text-green-600' : 'text-red-600'}>
            {record.change24h >= 0 ? '+' : ''}${record.change24h.toFixed(2)}
          </Text>
          <br />
          <Text className={`text-xs ${record.changePercent24h >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {record.changePercent24h >= 0 ? '+' : ''}{record.changePercent24h.toFixed(2)}%
          </Text>
        </div>
      )
    },
    {
      title: '24h成交量',
      dataIndex: 'volume24h',
      key: 'volume24h',
      render: (value: number) => `$${(value / 1000000000).toFixed(2)}B`
    },
    {
      title: '市值',
      dataIndex: 'marketCap',
      key: 'marketCap',
      render: (value: number) => `$${(value / 1000000000).toFixed(2)}B`
    },
    {
      title: '24h最高/最低',
      key: 'highLow',
      render: (_: any, record: MarketData) => (
        <div>
          <Text className="text-green-600">${record.high24h.toLocaleString()}</Text>
          <br />
          <Text className="text-red-600">${record.low24h.toLocaleString()}</Text>
        </div>
      )
    }
  ]

  // 技术指标表格列配置
  const indicatorColumns = [
    {
      title: '指标',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: '数值',
      dataIndex: 'value',
      key: 'value',
      render: (value: number, record: TechnicalIndicator) => {
        if (record.name.includes('MA') || record.name.includes('Bollinger')) {
          return `$${value.toLocaleString()}`
        }
        return value.toFixed(2)
      }
    },
    {
      title: '信号',
      dataIndex: 'signal',
      key: 'signal',
      render: (signal: string) => {
        const signalConfig = {
          buy: { color: 'green', text: '买入', icon: <ArrowUpOutlined /> },
          sell: { color: 'red', text: '卖出', icon: <ArrowDownOutlined /> },
          neutral: { color: 'orange', text: '中性', icon: <ThunderboltOutlined /> }
        }
        const config = signalConfig[signal as keyof typeof signalConfig]
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

  // 切换收藏
  const toggleFavorite = (symbol: string) => {
    setFavorites(prev => 
      prev.includes(symbol) 
        ? prev.filter(s => s !== symbol)
        : [...prev, symbol]
    )
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
          <Title level={2} className="!mb-2">市场分析</Title>
          <Text className="text-gray-500">实时市场数据分析和技术指标</Text>
        </div>
        <Space>
          <Button 
            icon={<ReloadOutlined />} 
            loading={loading}
            onClick={handleRefresh}
          >
            刷新
          </Button>
          <Button icon={<SettingOutlined />}>设置</Button>
        </Space>
      </div>

      {/* 市场统计 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="总市值"
              value={marketStats.totalMarketCap / 1000000000000}
              precision={2}
              prefix={<DollarOutlined className="text-blue-600" />}
              suffix="T USD"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="24h成交量"
              value={marketStats.totalVolume24h / 1000000000}
              precision={1}
              prefix={<BarChartOutlined className="text-green-600" />}
              suffix="B USD"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="BTC占比"
              value={marketStats.btcDominance}
              precision={1}
              prefix={<PieChartOutlined className="text-orange-500" />}
              suffix="%"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card">
            <div className="flex justify-between items-center">
              <div>
                <Text className="text-gray-500">恐慌贪婪指数</Text>
                <div className="text-2xl font-bold">{marketStats.fearGreedIndex}</div>
              </div>
              <div className={`text-right ${
                marketStats.fearGreedIndex <= 20 ? 'text-red-600' :
                marketStats.fearGreedIndex <= 40 ? 'text-orange-500' :
                marketStats.fearGreedIndex <= 60 ? 'text-yellow-500' :
                marketStats.fearGreedIndex <= 80 ? 'text-green-500' : 'text-green-600'
              }`}>
                <div className="text-sm">
                  {marketStats.fearGreedIndex <= 20 ? '极度恐慌' :
                   marketStats.fearGreedIndex <= 40 ? '恐慌' :
                   marketStats.fearGreedIndex <= 60 ? '中性' :
                   marketStats.fearGreedIndex <= 80 ? '贪婪' : '极度贪婪'}
                </div>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 主要内容区域 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card>
            <Tabs activeKey={activeTab} onChange={setActiveTab}>
              <TabPane tab="市场概览" key="overview">
                <div className="mb-4 flex justify-between items-center">
                  <Space>
                    <Input.Search
                      placeholder="搜索交易对"
                      style={{ width: 200 }}
                      prefix={<SearchOutlined />}
                    />
                    <Select defaultValue="all" style={{ width: 120 }}>
                      <Option value="all">全部</Option>
                      <Option value="favorites">收藏</Option>
                      <Option value="gainers">涨幅榜</Option>
                      <Option value="losers">跌幅榜</Option>
                    </Select>
                  </Space>
                  <Button icon={<FilterOutlined />}>筛选</Button>
                </div>
                <Table
                  columns={marketColumns}
                  dataSource={marketData}
                  rowKey="symbol"
                  pagination={{ pageSize: 10 }}
                  className="data-table"
                  scroll={{ x: 800 }}
                />
              </TabPane>
              
              <TabPane tab="K线图" key="chart">
                <div className="mb-4 flex justify-between items-center">
                  <Space>
                    <Select 
                      value={selectedSymbol} 
                      onChange={setSelectedSymbol}
                      style={{ width: 150 }}
                    >
                      {marketData.map(item => (
                        <Option key={item.symbol} value={item.symbol}>
                          {item.symbol}
                        </Option>
                      ))}
                    </Select>
                    <Select 
                      value={timeframe} 
                      onChange={setTimeframe}
                      style={{ width: 100 }}
                    >
                      <Option value="1m">1分钟</Option>
                      <Option value="5m">5分钟</Option>
                      <Option value="15m">15分钟</Option>
                      <Option value="1h">1小时</Option>
                      <Option value="4h">4小时</Option>
                      <Option value="1d">1天</Option>
                    </Select>
                  </Space>
                  <Space>
                    <span>显示成交量</span>
                    <Switch 
                      checked={showVolume} 
                      onChange={setShowVolume}
                      size="small"
                    />
                  </Space>
                </div>
                <ReactECharts 
                  option={candlestickOption} 
                  style={{ height: '500px' }} 
                />
              </TabPane>
              
              <TabPane tab="技术指标" key="indicators">
                <div className="mb-4">
                  <Alert
                    message="技术分析提醒"
                    description={`当前 ${selectedSymbol} 的技术指标显示混合信号，建议结合多个指标进行综合分析。`}
                    type="info"
                    showIcon
                    closable
                  />
                </div>
                <Table
                  columns={indicatorColumns}
                  dataSource={technicalIndicators}
                  rowKey="name"
                  pagination={false}
                  className="data-table"
                />
              </TabPane>
            </Tabs>
          </Card>
        </Col>
        
        <Col xs={24} lg={8}>
          <div className="space-y-4">
            {/* 市场分布 */}
            <Card title="市场份额分布" className="dashboard-card">
              <ReactECharts 
                option={marketDistributionOption} 
                style={{ height: '300px' }} 
              />
            </Card>
            
            {/* 恐慌贪婪指数 */}
            <Card title="恐慌贪婪指数" className="dashboard-card">
              <ReactECharts 
                option={fearGreedOption} 
                style={{ height: '250px' }} 
              />
            </Card>
            
            {/* 市场动态 */}
            <Card title="市场动态" className="dashboard-card">
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <Text>活跃币种</Text>
                  <Text strong>{marketStats.activeCoins.toLocaleString()}</Text>
                </div>
                <div className="flex justify-between items-center">
                  <Text className="text-green-600">上涨币种</Text>
                  <Text strong className="text-green-600">{marketStats.gainers}</Text>
                </div>
                <div className="flex justify-between items-center">
                  <Text className="text-red-600">下跌币种</Text>
                  <Text strong className="text-red-600">{marketStats.losers}</Text>
                </div>
                <div className="mt-4">
                  <Text className="text-gray-500">涨跌比例</Text>
                  <Progress 
                    percent={(marketStats.gainers / (marketStats.gainers + marketStats.losers)) * 100}
                    strokeColor="#22c55e"
                    trailColor="#ef4444"
                    showInfo={false}
                    className="mt-2"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>跌 {((marketStats.losers / (marketStats.gainers + marketStats.losers)) * 100).toFixed(1)}%</span>
                    <span>涨 {((marketStats.gainers / (marketStats.gainers + marketStats.losers)) * 100).toFixed(1)}%</span>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </Col>
      </Row>
    </div>
  )
}

export default MarketAnalysis