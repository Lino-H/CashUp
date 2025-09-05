import React, { useState, useEffect } from 'react';
import { Layout, Menu, Button, Card, Row, Col, Statistic, Typography, Space, Alert } from 'antd';
import { DashboardOutlined, LineChartOutlined, SettingOutlined, LoginOutlined, UserAddOutlined } from '@ant-design/icons';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import RealTimeTrading from './pages/RealTimeTrading';
import UserSettings from './pages/UserSettings';

const { Header, Sider, Content } = Layout;
const { Title, Paragraph } = Typography;

interface ServiceStatus {
  name: string;
  status: 'healthy' | 'unhealthy' | 'unknown';
  url: string;
}

// 主应用组件
const AppContent: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [services, setServices] = useState<ServiceStatus[]>([
    { name: '核心服务', status: 'unknown', url: '/api/core/health' },
    { name: '交易引擎', status: 'unknown', url: '/api/trading/health' },
    { name: '通知服务', status: 'unknown', url: '/api/notification/health' },
  ]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    checkServices();
    const interval = setInterval(checkServices, 30000); // 每30秒检查一次
    return () => clearInterval(interval);
  }, []);

  const checkServices = async () => {
    setLoading(true);
    const updatedServices = await Promise.all(
      services.map(async (service) => {
        try {
          const response = await fetch(service.url);
          const data = await response.json();
          return {
            ...service,
            status: data.status === 'healthy' ? 'healthy' : 'unhealthy'
          } as ServiceStatus;
        } catch (error) {
          return {
            ...service,
            status: 'unhealthy'
          } as ServiceStatus;
        }
      })
    );
    setServices(updatedServices);
    setLoading(false);
  };

  const healthyServices = services.filter(s => s.status === 'healthy').length;
  const totalServices = services.length;

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider trigger={null} collapsible collapsed={collapsed}>
        <div style={{ 
          height: 32, 
          margin: 16, 
          background: 'rgba(255, 255, 255, 0.3)',
          borderRadius: 6,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontWeight: 'bold'
        }}>
          {collapsed ? 'CU' : 'CashUp'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname === '/trading' ? 'trading' : location.pathname === '/settings' ? 'settings' : 'dashboard']}
          items={[
            {
              key: 'dashboard',
              icon: <DashboardOutlined />,
              label: '仪表板',
              onClick: () => navigate('/')
            },
            {
              key: 'trading',
              icon: <LineChartOutlined />,
              label: '实时交易',
              onClick: () => navigate('/trading')
            },
            {
              key: 'settings',
              icon: <SettingOutlined />,
              label: '系统设置',
              onClick: () => navigate('/settings')
            },
          ]}
        />
      </Sider>
      
      <Layout>
        <Header style={{ 
          padding: 0, 
          background: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingRight: 24
        }}>
          <div style={{ padding: '0 24px' }}>
            <Title level={3} style={{ margin: 0, color: '#001529' }}>
              CashUp 量化交易平台 v2
            </Title>
          </div>
          <Space>
            <Button 
              type="primary" 
              icon={<LoginOutlined />}
              onClick={() => navigate('/login')}
            >
              登录
            </Button>
            <Button 
              icon={<UserAddOutlined />}
              onClick={() => navigate('/register')}
            >
              注册
            </Button>
          </Space>
        </Header>
        
        <Content style={{ margin: '24px 16px', padding: 24, background: '#fff' }}>
          <Routes>
            <Route path="/" element={
              <div>
                <Row gutter={[16, 16]}>
                  <Col span={24}>
                    <Card>
                      <Title level={4}>系统状态</Title>
                      <Row gutter={16}>
                        <Col span={8}>
                          <Statistic 
                            title="运行中服务" 
                            value={healthyServices} 
                            suffix={`/ ${totalServices}`}
                            valueStyle={{ color: healthyServices === totalServices ? '#3f8600' : '#cf1322' }}
                          />
                        </Col>
                        <Col span={8}>
                          <Statistic 
                            title="系统状态" 
                            value={healthyServices === totalServices ? '正常' : '异常'} 
                            valueStyle={{ color: healthyServices === totalServices ? '#3f8600' : '#cf1322' }}
                          />
                        </Col>
                        <Col span={8}>
                          <Button loading={loading} onClick={checkServices}>
                            刷新状态
                          </Button>
                        </Col>
                      </Row>
                    </Card>
                  </Col>

                  {services.map((service) => (
                    <Col span={8} key={service.name}>
                      <Card>
                        <Statistic
                          title={service.name}
                          value={service.status === 'healthy' ? '正常' : service.status === 'unhealthy' ? '异常' : '未知'}
                          valueStyle={{ 
                            color: service.status === 'healthy' ? '#3f8600' : 
                                   service.status === 'unhealthy' ? '#cf1322' : '#d9d9d9' 
                          }}
                        />
                      </Card>
                    </Col>
                  ))}

                  <Col span={24}>
                    <Card>
                      <Title level={4}>欢迎使用 CashUp v2</Title>
                      <Paragraph>
                        CashUp 是一个专业的量化交易平台，提供策略开发、回测分析、实时交易等功能。
                      </Paragraph>
                      <Alert
                        message="系统信息"
                        description="当前系统正在运行中，所有核心服务状态正常。您可以使用上方按钮进行登录或注册。"
                        type="info"
                        showIcon
                      />
                    </Card>
                  </Col>
                </Row>
              </div>
            } />
            <Route path="/trading" element={<RealTimeTrading />} />
            <Route path="/settings" element={<UserSettings />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<LoginPage />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
};

// 主应用组件，包含Router
const App: React.FC = () => {
  return (
    <Router>
      <AppContent />
    </Router>
  );
};

export default App;