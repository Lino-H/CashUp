import React, { useEffect, useState } from 'react'
import { Card, Table, Button, Modal, Form, Input, Select, Switch, Space, message, Alert } from 'antd'
import { coreKeysAPI, coreExchangesAPI, handleApiError } from '../services/api'
/**
 * 函数集注释：
 * - load：加载现有密钥列表
 * - onSubmit：提交密钥并触发交易所重载
 * - handleSeedFromConfigs：从配置文件初始化密钥，错误友好提示
 * - handleReloadExchanges：重载交易所模块，错误友好提示
 */

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

  const handleSeedFromConfigs = async () => {
    try {
      await coreKeysAPI.seedFromConfigs()
      await coreKeysAPI.reloadExchanges()
      await load()
      message.success('初始化完成')
    } catch (e) {
      message.error(handleApiError(e))
    }
  }

  const handleReloadExchanges = async () => {
    try {
      await coreKeysAPI.reloadExchanges()
      message.success('重载成功')
    } catch (e) {
      message.error(handleApiError(e))
    }
  }

  const onSubmit = async () => {
    try {
      const v = await form.validateFields()
      const resp = await coreKeysAPI.upsert({ exchange: v.exchange, name: v.name || 'default', api_key: v.api_key, api_secret: v.api_secret, passphrase: v.passphrase, enabled: v.enabled })
      message.success('保存成功')
      setApplyAdvice((resp as any)?.apply || null)
      setVisible(false)
      form.resetFields()
      try {
        await coreKeysAPI.reloadExchanges()
      } catch (e) {
        message.warning('密钥已保存，但重载交易所失败，请稍后重试')
      }
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
          <Button onClick={handleSeedFromConfigs}>从配置初始化</Button>
          <Button onClick={handleReloadExchanges}>重载交易所</Button>
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