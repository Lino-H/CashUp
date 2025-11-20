import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Card, message, Tabs, Typography, Row, Col, Checkbox } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '../services/api';

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

// 函数集注释：
// 1) handleLogin：提交登录表单，处理记住用户名与导航
// 2) handleRegister：提交注册表单，处理注册成功切换到登录
// 3) useEffect 初始化：读取本地记住的用户名填充初始值

const LoginPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('login');
  const [rememberMe, setRememberMe] = useState(false);
  const [initialValues, setInitialValues] = useState<Partial<LoginForm>>({});
  const { login } = useAuth();
  const navigate = useNavigate();

  // 初始化时检查是否有记住的用户名
  useEffect(() => {
    const rememberedUsername = localStorage.getItem('remembered_username');
    if (rememberedUsername) {
      setInitialValues({
        username: rememberedUsername,
      });
      setRememberMe(true);
    }
  }, []);

  const handleLogin = async (values: LoginForm) => {
    setLoading(true);
    try {
      await login(values.username, values.password);
      
      // 如果选择了记住密码，保存用户名
      if (rememberMe) {
        localStorage.setItem('remembered_username', values.username);
      } else {
        localStorage.removeItem('remembered_username');
      }
      
      message.success('登录成功！');
      navigate('/');
    } catch (error: any) {
      const errorMessage = error?.response?.status === 401
        ? '用户名或密码错误'
        : (error?.message || '请求失败');
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (values: RegisterForm) => {
    setLoading(true);
    try {
      // 移除confirm_password字段
      const { confirm_password, ...registerData } = values;
      
      const response = await authAPI.register(registerData);
      
      if (response) {
        message.success('注册成功！请登录');
        setActiveTab('login');
      }
    } catch (error: any) {
      const errorMessage = error?.response?.status === 400
        ? '注册信息有误'
        : (error?.message || '注册失败');
      message.error(errorMessage);
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
                    initialValues={initialValues}
                    autoComplete="off"
                    size="large"
                    data-testid="login-form"
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
                      <Form.Item name="remember" valuePropName="checked" noStyle>
                        <Checkbox 
                          checked={rememberMe}
                          onChange={(e) => setRememberMe(e.target.checked)}
                        >
                          记住用户名
                        </Checkbox>
                      </Form.Item>
                    </Form.Item>

                    <Form.Item>
                      <Button 
                        type="primary" 
                        htmlType="submit" 
                        loading={loading}
                        disabled={loading}
                        aria-disabled={loading}
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
                    data-testid="register-form"
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
                        disabled={loading}
                        aria-disabled={loading}
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
