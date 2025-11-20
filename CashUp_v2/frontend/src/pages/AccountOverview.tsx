import React, { useCallback, useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Table, Tag, Divider, Select, Space, Switch, InputNumber, Button } from 'antd'
import { DollarCircleOutlined, ReloadOutlined, DownloadOutlined, PictureOutlined } from '@ant-design/icons'
import { coreReportingAPI, coreTradingAPI, handleApiError } from '../services/api'
import { ResponsiveContainer, ComposedChart, CartesianGrid, XAxis, YAxis, Tooltip as RechartsTooltip, Line, AreaChart, Area } from 'recharts'

const AccountOverview: React.FC = () => {
  const [overview, setOverview] = useState<any[]>([])
  const [positions, setPositions] = useState<any[]>([])
  const [selectedExchange, setSelectedExchange] = useState<string>('')
  const [autoRefresh, setAutoRefresh] = useState<boolean>(false)
  const [refreshInterval, setRefreshInterval] = useState<number>(30)
  const [equityData, setEquityData] = useState<any[]>([])
  const [winrateData, setWinrateData] = useState<any[]>([])
  const [aggMode, setAggMode] = useState<boolean>(false)
  const [aggEquityData, setAggEquityData] = useState<any[]>([])
  const [aggWinrateData, setAggWinrateData] = useState<any[]>([])

  const computeSeries = (items: any[]) => {
    const closed = items.filter((x) => x.status === 'closed').sort((a, b) => new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime())
    let s = 0
    let wins = 0
    let total = 0
    const eq: any[] = []
    const wr: any[] = []
    closed.forEach((r) => {
      s += Number(r.realized_pnl || 0)
      total += 1
      if (Number(r.realized_pnl || 0) > 0) wins += 1
      const rate = total > 0 ? (wins / total) * 100 : 0
      eq.push({ date: r.updated_at, equity: s })
      wr.push({ date: r.updated_at, winRate: rate })
    })
    setEquityData(eq)
    setWinrateData(wr)
  }

  const refreshData = useCallback(async (exchange?: string) => {
    try {
      const ov = await coreReportingAPI.accountOverview()
      const data = ov?.data || []
      setOverview(data)
      const ex = exchange || selectedExchange || (data[0]?.exchange || '')
      if (ex) {
        setSelectedExchange(ex)
        const p = await coreTradingAPI.positions(ex)
        const items = p?.data || []
        setPositions(items)
        computeSeries(items)
      }
      if (data && data.length > 0) {
        // 汇总模式：并发获取每个交易所的持仓并合并
        const allPositions: any[] = []
        const promises = data.map((ov: any) => coreTradingAPI.positions(ov.exchange).then((r) => (r?.data || [])).catch(() => []))
        const results = await Promise.all(promises)
        results.forEach((arr) => { allPositions.push(...arr) })
        // 生成汇总序列
        const closed = allPositions.filter((x) => x.status === 'closed').sort((a, b) => new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime())
        let s = 0
        let wins = 0
        let total = 0
        const eq: any[] = []
        const wr: any[] = []
        closed.forEach((r) => {
          s += Number(r.realized_pnl || 0)
          total += 1
          if (Number(r.realized_pnl || 0) > 0) wins += 1
          const rate = total > 0 ? (wins / total) * 100 : 0
          eq.push({ date: r.updated_at, equity: s })
          wr.push({ date: r.updated_at, winRate: rate })
        })
        setAggEquityData(eq)
        setAggWinrateData(wr)
      }
    } catch (e) {
      console.error(handleApiError(e))
    }
  }, [selectedExchange])

  useEffect(() => { refreshData() }, [refreshData])

  useEffect(() => {
    let interval: any
    if (autoRefresh) {
      interval = setInterval(() => { refreshData(selectedExchange) }, refreshInterval * 1000)
    }
    return () => { if (interval) clearInterval(interval) }
  }, [autoRefresh, refreshInterval, selectedExchange, refreshData])

  const columns = [
    { title: '交易所', dataIndex: 'exchange', key: 'exchange' },
    { title: '交易对', dataIndex: 'symbol', key: 'symbol', render: (v: string) => <Tag color="blue">{v}</Tag> },
    { title: '方向', dataIndex: 'side', key: 'side', render: (v: string) => <Tag color={v === 'long' ? 'green' : 'red'}>{v}</Tag> },
    { title: '数量', dataIndex: 'quantity', key: 'quantity' },
    { title: '开仓价', dataIndex: 'entry_price', key: 'entry_price' },
    { title: '标记价', dataIndex: 'mark_price', key: 'mark_price' },
    { title: '浮盈', dataIndex: 'unrealized_pnl', key: 'unrealized_pnl' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => <Tag>{v}</Tag> },
  ]

  return (
    <div style={{ padding: 24 }}>
      <Space style={{ marginBottom: 16 }}>
        <Select
          placeholder="选择交易所"
          style={{ width: 200 }}
          value={selectedExchange || undefined}
          onChange={(v) => refreshData(v)}
          options={(overview || []).map((ov) => ({ label: ov.exchange, value: ov.exchange }))}
        />
        <Switch checkedChildren="自动刷新" unCheckedChildren="手动刷新" checked={autoRefresh} onChange={setAutoRefresh} />
        {autoRefresh && (
          <InputNumber min={5} max={300} value={refreshInterval} onChange={(v) => setRefreshInterval(Number(v))} addonAfter="秒" />
        )}
        <Button icon={<ReloadOutlined />} onClick={() => refreshData(selectedExchange)}>刷新</Button>
        <Switch checkedChildren="汇总视图" unCheckedChildren="单所视图" checked={aggMode} onChange={setAggMode} />
        <Button icon={<DownloadOutlined />} onClick={() => {
          const rows = (aggMode ? aggEquityData : equityData).map((d) => `${d.date},${d.equity}`)
          const csv = `date,equity\n${rows.join('\n')}`
          const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `equity_${aggMode ? 'combined' : selectedExchange || 'default'}.csv`
          a.click()
          URL.revokeObjectURL(url)
        }}>导出权益CSV</Button>
        <Button icon={<DownloadOutlined />} onClick={() => {
          const rows = (aggMode ? aggWinrateData : winrateData).map((d) => `${d.date},${d.winRate}`)
          const csv = `date,winRate\n${rows.join('\n')}`
          const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `winrate_${aggMode ? 'combined' : selectedExchange || 'default'}.csv`
          a.click()
          URL.revokeObjectURL(url)
        }}>导出胜率CSV</Button>
        <Button icon={<PictureOutlined />} onClick={() => {
          const el = document.getElementById('equity-chart')
          if (!el) return
          const svg = el.querySelector('svg')
          if (!svg) return
          const data = new XMLSerializer().serializeToString(svg as any)
          const blob = new Blob([data], { type: 'image/svg+xml;charset=utf-8' })
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `equity_${aggMode ? 'combined' : selectedExchange || 'default'}.svg`
          a.click()
          URL.revokeObjectURL(url)
        }}>导出权益SVG</Button>
        <Button icon={<PictureOutlined />} onClick={() => {
          const el = document.getElementById('winrate-chart')
          if (!el) return
          const svg = el.querySelector('svg')
          if (!svg) return
          const data = new XMLSerializer().serializeToString(svg as any)
          const blob = new Blob([data], { type: 'image/svg+xml;charset=utf-8' })
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `winrate_${aggMode ? 'combined' : selectedExchange || 'default'}.svg`
          a.click()
          URL.revokeObjectURL(url)
        }}>导出胜率SVG</Button>
      </Space>
      <Row gutter={[16, 16]}>
        {overview.map((ov, idx) => (
          <Col xs={24} sm={12} md={6} key={idx}>
            <Card>
              <Statistic title={`账户(${ov.exchange})余额`} value={ov.total_balance} precision={2} prefix={<DollarCircleOutlined />} />
              <Divider style={{ margin: 8 }} />
              <Statistic title="可用" value={ov.total_available} precision={2} />
              <Statistic title="浮盈" value={ov.total_unrealized_pnl} precision={2} valueStyle={{ color: (ov.total_unrealized_pnl || 0) >= 0 ? '#3f8600' : '#cf1322' }} />
            </Card>
          </Col>
        ))}
      </Row>
      <Divider />
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Card title="权益曲线">
            <div id="equity-chart">
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={aggMode ? aggEquityData : equityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <RechartsTooltip />
                <Area type="monotone" dataKey="equity" stroke="#8884d8" fill="#8884d8" fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
            </div>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="胜率趋势">
            <div id="winrate-chart">
            <ResponsiveContainer width="100%" height={200}>
              <ComposedChart data={aggMode ? aggWinrateData : winrateData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <RechartsTooltip />
                <Line type="monotone" dataKey="winRate" stroke="#ff7300" />
              </ComposedChart>
            </ResponsiveContainer>
            </div>
          </Card>
        </Col>
      </Row>
      <Card title="持仓">
        <Table columns={columns} dataSource={positions} rowKey="id" pagination={{ pageSize: 10 }} />
      </Card>
    </div>
  )
}

export default AccountOverview
