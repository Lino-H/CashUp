import React, { useState, useEffect } from 'react';
import { Layout, Menu, Button, Card, Row, Col, Statistic, Typography, Space, Alert, Avatar, Dropdown } from 'antd';
import { DashboardOutlined, LineChartOutlined, SettingOutlined, LoginOutlined, UserAddOutlined, LogoutOutlined, UserOutlined, BarChartOutlined, FundOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { ErrorBoundary } from './components/ErrorBoundary';
import LoginPage from './pages/LoginPage';
import RealTimeTrading from './pages/RealTimeTrading';
import RealTimeTradingWebSocket from './pages/RealTimeTradingWebSocket';
import StrategyManagement from './pages/StrategyManagement';
import TradingManagement from './pages/TradingManagement';
import UserSettings from './pages/UserSettings';
import NetworkOptimizationDemo from './pages/NetworkOptimizationDemo';

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
    { name: '核心服务', status: 'unknown', url: 'http://localhost:8001/health' },
    { name: '交易引擎', status: 'unknown', url: 'http://localhost:8002/health' },
    { name: '策略平台', status: 'unknown', url: 'http://localhost:8003/health' },
    { name: '通知服务', status: 'unknown', url: 'http://localhost:8004/health' },
  ]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAuthenticated, logout } = useAuth();

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
          selectedKeys={[location.pathname === '/trading' ? 'trading' : location.pathname === '/trading-management' ? 'trading-management' : location.pathname === '/strategies' ? 'strategies' : location.pathname === '/settings' ? 'settings' : location.pathname === '/network-optimization' ? 'network-optimization' : location.pathname === '/websocket-trading' ? 'websocket-trading' : 'dashboard']}
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
              key: 'trading-management',
              icon: <FundOutlined />,
              label: '交易管理',
              onClick: () => navigate('/trading-management')
            },
            {
              key: 'websocket-trading',
              icon: <ThunderboltOutlined />,
              label: 'WebSocket交易',
              onClick: () => navigate('/websocket-trading')
            },
            {
              key: 'strategies',
              icon: <BarChartOutlined />,
              label: '策略管理',
              onClick: () => navigate('/strategies')
            },
            {
              key: 'settings',
              icon: <SettingOutlined />,
              label: '系统设置',
              onClick: () => navigate('/settings')
            },
            {
              key: 'network-optimization',
              icon: <BarChartOutlined />,
              label: '网络优化',
              onClick: () => navigate('/network-optimization')
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
            {isAuthenticated && user ? (
              <Dropdown 
                menu={{
                  items: [
                    {
                      key: 'profile',
                      label: '个人信息',
                      icon: <UserOutlined />,
                    },
                    {
                      key: 'logout',
                      label: '退出登录',
                      icon: <LogoutOutlined />,
                      onClick: () => {
                        logout();
                        navigate('/login');
                      },
                    },
                  ],
                }}
                placement="bottomRight"
              >
                <Button icon={<UserOutlined />}>
                  {user.username || user.full_name}
                </Button>
              </Dropdown>
            ) : (
              <>
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
              </>
            )}
          </Space>
        </Header>
        
        <Content style={{ margin: '24px 16px', padding: 24, background: '#fff' }}>
          <Routes>
            <Route path="/" element={
              <ProtectedRoute>
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
                          description={`当前系统正在运行中，所有核心服务状态正常。欢迎回来，${user?.username || user?.full_name || '用户'}！`}
                          type="info"
                          showIcon
                        />
                      </Card>
                    </Col>
                  </Row>
                </div>
              </ProtectedRoute>
            } />
            <Route path="/trading" element={
              <ProtectedRoute>
                <RealTimeTrading />
              </ProtectedRoute>
            } />
            <Route path="/trading-management" element={
              <ProtectedRoute>
                <TradingManagement />
              </ProtectedRoute>
            } />
            <Route path="/websocket-trading" element={
              <ProtectedRoute>
                <RealTimeTradingWebSocket />
              </ProtectedRoute>
            } />
            <Route path="/strategies" element={
              <ProtectedRoute>
                <StrategyManagement />
              </ProtectedRoute>
            } />
            <Route path="/settings" element={
              <ProtectedRoute>
                <UserSettings />
              </ProtectedRoute>
            } />
            <Route path="/network-optimization" element={
              <ProtectedRoute>
                <NetworkOptimizationDemo />
              </ProtectedRoute>
            } />
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
    <ErrorBoundary>
      <AuthProvider>
        <Router>
          <AppContent />
        </Router>
      </AuthProvider>
    </ErrorBoundary>
  );
};

export default App;