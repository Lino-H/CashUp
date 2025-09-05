import React, { useState } from 'react';
import { Form, Input, Button, Card, message, Tabs, Typography, Row, Col } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

interface LoginForm {
  username: string;
  password: string;
}

interface RegisterForm {
  username: string;
  email: string;
  password: string;
  confirm_password: string;
  full_name?: string;
}

const LoginPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('login');

  const handleLogin = async (values: LoginForm) => {
    setLoading(true);
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(values),
      });

      if (response.ok) {
        const data = await response.json();
        message.success('登录成功！');
        // 存储token
        localStorage.setItem('token', data.access_token);
        // 跳转到首页
        window.location.href = '/';
      } else {
        const error = await response.json();
        message.error(error.message || '登录失败');
      }
    } catch (error) {
      message.error('网络错误，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (values: RegisterForm) => {
    setLoading(true);
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(values),
      });

      if (response.ok) {
        message.success('注册成功！请登录');
        setActiveTab('login');
      } else {
        const error = await response.json();
        message.error(error.message || '注册失败');
      }
    } catch (error) {
      message.error('网络错误，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Row justify="center" align="middle" style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Col xs={22} sm={18} md={12} lg={8} xl={6}>
        <Card>
          <div style={{ textAlign: 'center', marginBottom: 24 }}>
            <Title level={2} style={{ color: '#1890ff', margin: 0 }}>
              CashUp
            </Title>
            <Text type="secondary">量化交易平台</Text>
          </div>

          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            centered
            items={[
              {
                key: 'login',
                label: '登录',
                children: (
                  <Form
                    name="login"
                    onFinish={handleLogin}
                    autoComplete="off"
                    size="large"
                  >
                    <Form.Item
                      name="username"
                      rules={[{ required: true, message: '请输入用户名!' }]}
                    >
                      <Input 
                        prefix={<UserOutlined />} 
                        placeholder="用户名" 
                      />
                    </Form.Item>

                    <Form.Item
                      name="password"
                      rules={[{ required: true, message: '请输入密码!' }]}
                    >
                      <Input.Password 
                        prefix={<LockOutlined />} 
                        placeholder="密码" 
                      />
                    </Form.Item>

                    <Form.Item>
                      <Button 
                        type="primary" 
                        htmlType="submit" 
                        loading={loading}
                        style={{ width: '100%' }}
                      >
                        登录
                      </Button>
                    </Form.Item>
                  </Form>
                )
              },
              {
                key: 'register',
                label: '注册',
                children: (
                  <Form
                    name="register"
                    onFinish={handleRegister}
                    autoComplete="off"
                    size="large"
                  >
                    <Form.Item
                      name="username"
                      rules={[{ required: true, message: '请输入用户名!' }]}
                    >
                      <Input 
                        prefix={<UserOutlined />} 
                        placeholder="用户名" 
                      />
                    </Form.Item>

                    <Form.Item
                      name="email"
                      rules={[
                        { required: true, message: '请输入邮箱!' },
                        { type: 'email', message: '请输入有效的邮箱地址!' }
                      ]}
                    >
                      <Input 
                        prefix={<MailOutlined />} 
                        placeholder="邮箱" 
                      />
                    </Form.Item>

                    <Form.Item
                      name="password"
                      rules={[
                        { required: true, message: '请输入密码!' },
                        { min: 6, message: '密码至少6位!' }
                      ]}
                    >
                      <Input.Password 
                        prefix={<LockOutlined />} 
                        placeholder="密码" 
                      />
                    </Form.Item>

                    <Form.Item
                      name="confirm_password"
                      dependencies={['password']}
                      rules={[
                        { required: true, message: '请确认密码!' },
                        ({ getFieldValue }) => ({
                          validator(_, value) {
                            if (!value || getFieldValue('password') === value) {
                              return Promise.resolve();
                            }
                            return Promise.reject(new Error('两次输入的密码不一致!'));
                          },
                        }),
                      ]}
                    >
                      <Input.Password 
                        prefix={<LockOutlined />} 
                        placeholder="确认密码" 
                      />
                    </Form.Item>

                    <Form.Item
                      name="full_name"
                      rules={[{ required: true, message: '请输入姓名!' }]}
                    >
                      <Input placeholder="姓名" />
                    </Form.Item>

                    <Form.Item>
                      <Button 
                        type="primary" 
                        htmlType="submit" 
                        loading={loading}
                        style={{ width: '100%' }}
                      >
                        注册
                      </Button>
                    </Form.Item>
                  </Form>
                )
              }
            ]}
          />
        </Card>
      </Col>
    </Row>
  );
};

export default LoginPage;