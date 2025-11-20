import React, { useEffect, useState } from 'react'
import { Card, Row, Col, Table, Button, Space, Form, InputNumber, Input, message, Tag, Select } from 'antd'
import { ResponsiveContainer, LineChart, CartesianGrid, XAxis, YAxis, Tooltip as RechartsTooltip, Line } from 'recharts'
import { coreSchedulerAPI, coreRSSAPI, handleApiError } from '../services/api'
/**
 * 函数集注释：
 * - load: 拉取调度状态数据
 * - save: 保存任务间隔与备用RSS
 * - fmt: 格式化时间戳
 * 页面功能：调度任务状态、错误与市场错误趋势、触发历史与快捷触发
 */

const SchedulerMonitor: React.FC = () => {
  const [data, setData] = useState<any>({ intervals: {}, last: {} })
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()
  const [granularity, setGranularity] = useState<'hour'|'day'>('hour')
  const [selectedTask, setSelectedTask] = useState<string | undefined>(undefined)
  const [selectedFeed, setSelectedFeed] = useState<string | undefined>(undefined)
  const [feedOptions, setFeedOptions] = useState<any[]>([])

  const load = React.useCallback(async () => {
    setLoading(true)
    try {
      const resp = await coreSchedulerAPI.status({ params: { granularity, task: selectedTask, feed_id: selectedFeed } })
      setData(resp?.data || { intervals: {}, last: {} })
    } catch (e) {
      message.error(handleApiError(e))
    } finally {
      setLoading(false)
    }
  }, [granularity, selectedTask, selectedFeed])

  useEffect(() => { load() }, [load])

  useEffect(() => {
    coreRSSAPI.listFeeds().then((resp) => {
      const items = resp?.data || []
      setFeedOptions((items || []).map((it: any) => ({ label: `${it.name || 'feed'} (${it.id})`, value: it.id })))
    }).catch(() => {})
  }, [])

  const intervals = data.intervals || {}
  const last = data.last || {}
  const errors = data.errors || { total: 0, last: null, per_feed: {} }
  const fallback = data.fallback || []
  const history = data.history || []
  const errorSeries = (data.error_series || []).map((p: any) => ({ time: new Date(Number(p.bucket) * 1000).toLocaleString(), count: p.count }))
  const marketErrors = data.errors?.market_last ? new Date(Number(data.errors.market_last) * 1000).toLocaleString() : '-'
  const marketErrorSeries = (data.market_error_series || []).map((p: any) => ({ time: new Date(Number(p.bucket) * 1000).toLocaleString(), count: p.count }))
  const taskSeriesRaw = (data.task_series || []) as any[]
  const taskSeries = selectedTask
    ? (taskSeriesRaw.find((t: any) => t.name === selectedTask)?.points || []).map((p: any) => ({ time: new Date(Number(p.bucket) * 1000).toLocaleString(), count: p.count }))
    : []

  const save = async () => {
    try {
      const v = await form.validateFields()
      const updates = [
        ['rss.fetch.interval', v.rssFetch],
        ['rss.analyze.interval', v.rssAnalyze],
        ['rss.correlation.interval', v.rssCorrelation],
        ['trading.sync.interval', v.tradingSync],
      ]
      for (const [k, val] of updates) {
        if (val !== undefined && val !== null) {
          await coreSchedulerAPI.setInterval(k, Number(val))
        }
      }
      if (v.fallbackRaw) {
        const urls = String(v.fallbackRaw).split(',').map(s => s.trim()).filter(Boolean)
        await coreSchedulerAPI.setFallback(urls)
      }
      message.success('保存成功')
      load()
    } catch (e) {
      message.error(handleApiError(e))
    }
  }

  const cols = [
    { title: '任务', dataIndex: 'task', key: 'task' },
    { title: '间隔(秒)', dataIndex: 'interval', key: 'interval' },
    { title: '最近触发时间戳', dataIndex: 'last', key: 'last' },
  ]
  const fmt = (ts: any) => {
    if (!ts || ts === '-') return '-'
    const d = new Date(Number(ts) * 1000)
    return d.toLocaleString()
  }
  const rows = [
    { task: 'rss.fetch', interval: intervals['rss.fetch.interval'], last: fmt(last['rss.fetch']) },
    { task: 'rss.analyze', interval: intervals['rss.analyze.interval'], last: fmt(last['rss.analyze']) },
    { task: 'rss.correlation', interval: intervals['rss.correlation.interval'], last: fmt(last['rss.correlation']) },
    { task: 'trading.sync', interval: intervals['trading.sync.interval'], last: fmt(last['trading.sync']) },
  ]

  return (
    <div style={{ padding: 24 }}>
      <Card title="调度监控" loading={loading}>
        <Table columns={cols} dataSource={rows} pagination={false} rowKey={(r) => r.task} style={{ marginBottom: 16 }} />
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={12}>
            <Card title="错误统计">
              <Space direction="vertical">
                <div>总错误次数: <Tag color={errors.total > 0 ? 'red' : 'green'}>{errors.total}</Tag></div>
                <div>最后错误时间: {errors.last ? new Date(Number(errors.last) * 1000).toLocaleString() : '-'}</div>
                <div>按源统计: {Object.entries(errors.per_feed || {}).map(([k,v]: any) => (<Tag key={k}>{k}:{v}</Tag>))}</div>
                <div>市场错误最后时间: {marketErrors}</div>
                <div>
                  粒度:
                  <Select value={granularity} style={{ width: 160, marginLeft: 8 }} onChange={(v) => setGranularity(v as any)} options={[{ label: '小时', value: 'hour' }, { label: '天', value: 'day' }]} />
                </div>
                <div>
                  任务筛选:
                  <Select allowClear value={selectedTask} style={{ width: 220, marginLeft: 8 }} onChange={(v) => setSelectedTask(v)} options={[
                    { label: 'RSS抓取', value: 'rss.fetch' },
                    { label: 'RSS分析', value: 'rss.analyze' },
                    { label: 'RSS关联', value: 'rss.correlation' },
                    { label: '交易同步', value: 'trading.sync' },
                    { label: '行情采集', value: 'market.collect' },
                  ]} />
                </div>
                <div>
                  源筛选:
                  <Select allowClear value={selectedFeed} style={{ width: 280, marginLeft: 8 }} onChange={(v) => setSelectedFeed(v)} options={feedOptions} />
                </div>
              </Space>
            </Card>
          </Col>
          <Col span={12}>
            <Card title="备用RSS源">
              <Space direction="vertical">
                <div>当前备用: {(fallback || []).map((u: string) => (<Tag key={u}>{u}</Tag>))}</div>
              </Space>
            </Card>
          </Col>
        </Row>
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={24}>
            <Card title="触发历史">
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={history.map((h: any) => ({ ...h, time: new Date(h.timestamp * 1000).toLocaleTimeString() }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <RechartsTooltip />
                  <Line type="monotone" dataKey="timestamp" stroke="#8884d8" />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        </Row>
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={24}>
            <Card title="错误趋势">
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={errorSeries}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <RechartsTooltip />
                  <Line type="monotone" dataKey="count" stroke="#cf1322" />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        </Row>
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={24}>
            <Card title="任务趋势（按筛选任务）">
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={taskSeries}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <RechartsTooltip />
                  <Line type="monotone" dataKey="count" stroke="#52c41a" />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        </Row>
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={24}>
            <Card title="市场错误趋势">
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={marketErrorSeries}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <RechartsTooltip />
                  <Line type="monotone" dataKey="count" stroke="#722ed1" />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        </Row>
        <Form form={form} layout="inline">
          <Space wrap>
            <Form.Item name="rssFetch" label="RSS抓取">
              <InputNumber min={30} max={3600} placeholder={String(intervals['rss.fetch.interval'] || '')} />
            </Form.Item>
            <Form.Item name="rssAnalyze" label="RSS分析">
              <InputNumber min={60} max={3600} placeholder={String(intervals['rss.analyze.interval'] || '')} />
            </Form.Item>
            <Form.Item name="rssCorrelation" label="RSS关联">
              <InputNumber min={60} max={3600} placeholder={String(intervals['rss.correlation.interval'] || '')} />
            </Form.Item>
            <Form.Item name="tradingSync" label="交易同步">
              <InputNumber min={10} max={600} placeholder={String(intervals['trading.sync.interval'] || '')} />
            </Form.Item>
            <Form.Item name="fallbackRaw" label="备用RSS(逗号分隔)">
              <Input placeholder={fallback.join(',')} style={{ width: 400 }} />
            </Form.Item>
            <Button type="primary" onClick={save}>保存间隔</Button>
            <Button onClick={load}>刷新</Button>
            <Button onClick={async () => { await coreSchedulerAPI.trigger('rss.fetch'); message.success('已触发RSS抓取'); load() }}>触发RSS抓取</Button>
            <Button onClick={async () => { await coreSchedulerAPI.trigger('rss.analyze'); message.success('已触发RSS分析'); load() }}>触发RSS分析</Button>
            <Button onClick={async () => { await coreSchedulerAPI.trigger('rss.correlation'); message.success('已触发RSS关联'); load() }}>触发RSS关联</Button>
            <Button onClick={async () => { await coreSchedulerAPI.trigger('trading.sync'); message.success('已触发交易同步'); load() }}>触发交易同步</Button>
            <Button onClick={async () => { await coreSchedulerAPI.trigger('market.collect'); message.success('已触发行情采集'); load() }}>触发行情采集</Button>
          </Space>
        </Form>
      </Card>
    </div>
  )
}

export default SchedulerMonitor
