import React, { useEffect, useState } from 'react'
import { Card, Table, Button, Modal, Form, Input, Select, Switch, Space, message, Alert } from 'antd'
import { coreKeysAPI, coreExchangesAPI, handleApiError } from '../services/api'

const KeysManagement: React.FC = () => {
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [visible, setVisible] = useState(false)
  const [exchangeOptions, setExchangeOptions] = useState<any[]>([])
  const [applyAdvice, setApplyAdvice] = useState<any>(null)
  const [form] = Form.useForm()

  const load = async () => {
    setLoading(true)
    try {
      const resp = await coreKeysAPI.list()
      setItems(resp?.data || [])
    } catch (e) {
      message.error(handleApiError(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  useEffect(() => {
    coreExchangesAPI.list().then((resp) => {
      const names = resp?.data || []
      setExchangeOptions((names || []).map((n: string) => ({ label: n, value: n })))
    }).catch(() => {})
  }, [])

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: '交易所', dataIndex: 'exchange', key: 'exchange' },
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '启用', dataIndex: 'is_active', key: 'is_active', render: (v: boolean) => v ? '是' : '否' },
  ]

  const onSubmit = async () => {
    try {
      const v = await form.validateFields()
      const resp = await coreKeysAPI.upsert({ exchange: v.exchange, name: v.name || 'default', api_key: v.api_key, api_secret: v.api_secret, passphrase: v.passphrase, enabled: v.enabled })
      message.success('保存成功')
      setApplyAdvice(resp?.apply || null)
      setVisible(false)
      form.resetFields()
      await coreKeysAPI.reloadExchanges()
      load()
    } catch (e) {
      message.error(handleApiError(e))
    }
  }

  return (
    <div style={{ padding: 24 }}>
      <Card title="交易所密钥管理">
        <Space style={{ marginBottom: 16 }}>
          <Button type="primary" onClick={() => setVisible(true)}>新增/更新密钥</Button>
          <Button onClick={async () => { await coreKeysAPI.seedFromConfigs(); await coreKeysAPI.reloadExchanges(); load(); }}>从配置初始化</Button>
          <Button onClick={async () => { await coreKeysAPI.reloadExchanges(); message.success('重载成功'); }}>重载交易所</Button>
          <Button onClick={load} loading={loading}>刷新</Button>
        </Space>
        {applyAdvice && applyAdvice.type === 'reload' && (
          <Alert type="warning" message={`保存的密钥需要重载模块: ${applyAdvice.modules.join(', ')}`} action={<Button onClick={async () => { await coreKeysAPI.reloadExchanges(); setApplyAdvice(null); message.success('已重载'); }}>立即重载</Button>} style={{ marginBottom: 16 }} />
        )}
        <Table columns={columns} dataSource={items} rowKey={(r) => r.id || `${r.exchange}-${r.name}`} loading={loading} pagination={{ pageSize: 10 }} />
      </Card>
      <Modal open={visible} title="编辑密钥" onOk={onSubmit} onCancel={() => setVisible(false)} okText="保存" cancelText="取消">
        <Form form={form} layout="vertical">
          <Form.Item name="exchange" label="交易所" rules={[{ required: true, message: '请选择交易所' }]}>
            <Select options={exchangeOptions} />
          </Form.Item>
          <Form.Item name="name" label="名称">
            <Input placeholder="default" />
          </Form.Item>
          <Form.Item name="api_key" label="API Key" rules={[{ required: true, message: '请输入API Key' }, { min: 8, message: '长度至少8位' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="api_secret" label="API Secret" rules={[{ required: true, message: '请输入API Secret' }, { min: 8, message: '长度至少8位' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="passphrase" label="Passphrase">
            <Input />
          </Form.Item>
          <Form.Item name="enabled" label="启用" valuePropName="checked">
            <Switch defaultChecked />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default KeysManagement