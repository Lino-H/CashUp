import React, { useEffect, useState } from 'react'
import { Card, Table, Button, Modal, Form, Input, Switch, Space, message, Alert } from 'antd'
import { coreAdminAPI, coreKeysAPI, handleApiError } from '../services/api'

const ConfigCenter: React.FC = () => {
  const [configs, setConfigs] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [visible, setVisible] = useState(false)
  const [form] = Form.useForm()
  const [applyAdvice, setApplyAdvice] = useState<any>(null)

  const load = async () => {
    setLoading(true)
    try {
      const resp = await coreAdminAPI.listConfigs()
      setConfigs(resp?.data || [])
    } catch (e) {
      message.error(handleApiError(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const columns = [
    { title: '键', dataIndex: 'key', key: 'key' },
    { title: '值', dataIndex: 'value', key: 'value', render: (v: any) => typeof v === 'object' ? JSON.stringify(v) : String(v) },
    { title: '系统项', dataIndex: 'is_system', key: 'is_system', render: (v: boolean) => v ? '是' : '否' },
  ]

  const onSubmit = async () => {
    try {
      const values = await form.validateFields()
      const resp = await coreAdminAPI.setConfig(values.key, values.value, values.is_system)
      message.success('保存成功')
      setApplyAdvice((resp as any)?.apply || null)
      setVisible(false)
      form.resetFields()
      load()
    } catch (e) {
      message.error(handleApiError(e))
    }
  }

  return (
    <div style={{ padding: 24 }}>
      <Card title="系统配置">
        <Space style={{ marginBottom: 16 }}>
          <Button type="primary" onClick={() => setVisible(true)}>新增/更新配置</Button>
          <Button onClick={load} loading={loading}>刷新</Button>
        </Space>
        {applyAdvice && applyAdvice.type === 'reload' && (
          <Alert type="warning" message={`保存的配置需要重载模块: ${applyAdvice.modules.join(', ')}`} action={<Button onClick={async () => { if ((applyAdvice.modules || []).includes('exchanges')) await coreKeysAPI.reloadExchanges(); setApplyAdvice(null); message.success('已重载'); }}>立即重载</Button>} style={{ marginBottom: 16 }} />
        )}
        {applyAdvice && applyAdvice.type === 'immediate' && (
          <Alert type="success" message={`保存的配置已立即生效`} style={{ marginBottom: 16 }} />
        )}
        <Table columns={columns} dataSource={configs} rowKey={(r) => r.key} loading={loading} pagination={{ pageSize: 10 }} />
      </Card>
      <Modal open={visible} title="编辑配置" onOk={onSubmit} onCancel={() => setVisible(false)} okText="保存" cancelText="取消">
        <Form form={form} layout="vertical">
          <Form.Item name="key" label="键" rules={[{ required: true, message: '请输入键' }]}>
            <Input placeholder="如: trading.sync.interval" />
          </Form.Item>
          <Form.Item name="value" label="值" rules={[{ required: true, message: '请输入值' }]}>
            <Input placeholder="支持字符串或JSON" />
          </Form.Item>
          <Form.Item name="is_system" label="系统项" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ConfigCenter