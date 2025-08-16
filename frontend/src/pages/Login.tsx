import React, { useState } from 'react'
import { Form, Input, Button, Card, Typography, message, Checkbox, Divider } from 'antd'
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const { Title, Text, Link } = Typography

interface LoginForm {
  email: string
  password: string
  remember: boolean
}

interface RegisterForm {
  email: string
  password: string
  confirmPassword: string
  username: string
}

const Login: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const [form] = Form.useForm()

  const handleLogin = async (values: LoginForm) => {
    setLoading(true)
    try {
      // 模拟登录API调用
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // 模拟成功登录
      const mockToken = 'mock_jwt_token_' + Date.now()
      localStorage.setItem('access_token', mockToken)
      localStorage.setItem('user_info', JSON.stringify({
        id: '1',
        email: values.email,
        username: 'Demo User',
        avatar: 'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20avatar%20portrait&image_size=square'
      }))
      
      message.success('登录成功！')
      navigate('/dashboard')
    } catch (error) {
      message.error('登录失败，请检查用户名和密码')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (values: RegisterForm) => {
    setLoading(true)
    try {
      // 模拟注册API调用
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      message.success('注册成功！请登录')
      setIsLogin(true)
      form.resetFields()
    } catch (error) {
      message.error('注册失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  const handleDemoLogin = () => {
    form.setFieldsValue({
      email: 'demo@cashup.com',
      password: 'demo123',
      remember: true
    })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo和标题 */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-full mb-4">
            <span className="text-2xl font-bold text-white">C</span>
          </div>
          <Title level={2} className="!mb-2">CashUp</Title>
          <Text type="secondary">智能量化交易平台</Text>
        </div>

        <Card className="shadow-lg border-0">
          <div className="text-center mb-6">
            <Title level={3} className="!mb-2">
              {isLogin ? '登录账户' : '创建账户'}
            </Title>
            <Text type="secondary">
              {isLogin ? '欢迎回来，请登录您的账户' : '注册新账户开始交易'}
            </Text>
          </div>

          {isLogin ? (
            <Form
              form={form}
              name="login"
              onFinish={handleLogin}
              layout="vertical"
              size="large"
            >
              <Form.Item
                name="email"
                label="邮箱"
                rules={[
                  { required: true, message: '请输入邮箱' },
                  { type: 'email', message: '请输入有效的邮箱地址' }
                ]}
              >
                <Input
                  prefix={<MailOutlined />}
                  placeholder="请输入邮箱"
                />
              </Form.Item>

              <Form.Item
                name="password"
                label="密码"
                rules={[{ required: true, message: '请输入密码' }]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="请输入密码"
                />
              </Form.Item>

              <Form.Item>
                <div className="flex justify-between items-center">
                  <Form.Item name="remember" valuePropName="checked" noStyle>
                    <Checkbox>记住我</Checkbox>
                  </Form.Item>
                  <Link className="text-blue-600">忘记密码？</Link>
                </div>
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  className="w-full h-12 text-lg font-medium"
                >
                  登录
                </Button>
              </Form.Item>

              <Divider>或</Divider>

              <Button
                type="default"
                onClick={handleDemoLogin}
                className="w-full h-10 mb-4"
              >
                使用演示账户
              </Button>
            </Form>
          ) : (
            <Form
              form={form}
              name="register"
              onFinish={handleRegister}
              layout="vertical"
              size="large"
            >
              <Form.Item
                name="username"
                label="用户名"
                rules={[
                  { required: true, message: '请输入用户名' },
                  { min: 3, message: '用户名至少3个字符' }
                ]}
              >
                <Input
                  prefix={<UserOutlined />}
                  placeholder="请输入用户名"
                />
              </Form.Item>

              <Form.Item
                name="email"
                label="邮箱"
                rules={[
                  { required: true, message: '请输入邮箱' },
                  { type: 'email', message: '请输入有效的邮箱地址' }
                ]}
              >
                <Input
                  prefix={<MailOutlined />}
                  placeholder="请输入邮箱"
                />
              </Form.Item>

              <Form.Item
                name="password"
                label="密码"
                rules={[
                  { required: true, message: '请输入密码' },
                  { min: 6, message: '密码至少6个字符' }
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="请输入密码"
                />
              </Form.Item>

              <Form.Item
                name="confirmPassword"
                label="确认密码"
                dependencies={['password']}
                rules={[
                  { required: true, message: '请确认密码' },
                  ({ getFieldValue }) => ({
                    validator(_, value) {
                      if (!value || getFieldValue('password') === value) {
                        return Promise.resolve()
                      }
                      return Promise.reject(new Error('两次输入的密码不一致'))
                    },
                  }),
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="请再次输入密码"
                />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  className="w-full h-12 text-lg font-medium"
                >
                  注册
                </Button>
              </Form.Item>
            </Form>
          )}

          <div className="text-center mt-6">
            <Text type="secondary">
              {isLogin ? '还没有账户？' : '已有账户？'}
            </Text>
            <Link
              className="ml-2 text-blue-600 font-medium"
              onClick={() => {
                setIsLogin(!isLogin)
                form.resetFields()
              }}
            >
              {isLogin ? '立即注册' : '立即登录'}
            </Link>
          </div>
        </Card>

        {/* 底部信息 */}
        <div className="text-center mt-8 text-gray-500 text-sm">
          <div className="mb-2">
            <Link className="mx-2">服务条款</Link>
            <Link className="mx-2">隐私政策</Link>
            <Link className="mx-2">帮助中心</Link>
          </div>
          <Text type="secondary">© 2024 CashUp. All rights reserved.</Text>
        </div>
      </div>
    </div>
  )
}

export default Login