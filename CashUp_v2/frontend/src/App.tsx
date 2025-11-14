import React, { useState, useEffect } from 'react';
import { Layout, Menu, Button, Card, Row, Col, Statistic, Typography, Space, Alert, Avatar, Dropdown } from 'antd';
import { DashboardOutlined, LineChartOutlined, SettingOutlined, LoginOutlined, UserAddOutlined, LogoutOutlined, UserOutlined, BarChartOutlined, FundOutlined, ThunderboltOutlined, PieChartOutlined } from '@ant-design/icons';
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
import TechnicalAnalysisChart from './components/TechnicalAnalysisChart';
import FundamentalAnalysis from './components/FundamentalAnalysis';
import SentimentAnalysis from './components/SentimentAnalysis';
import RiskAnalysis from './components/RiskAnalysis';
import AutoTradingInterface from './components/AutoTradingInterface';
import StrategyAutomation from './components/StrategyAutomation';
import NewsPage from './pages/NewsPage';
import AccountOverview from './pages/AccountOverview';

const { Header, Sider, Content } = Layout;
const { Title, Paragraph } = Typography;

interface ServiceStatus {
  name: string;
  status: 'healthy' | 'unhealthy' | 'unknown';
  url: string;
}

interface AnalysisScores {
  technical: number;
  fundamental: number;
  sentiment: number;
  risk: number;
}

// 主应用组件
const AppContent: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [services, setServices] = useState<ServiceStatus[]>([
    { name: '核心服务', status: 'unknown', url: '/api/core/health' },
    { name: '交易引擎', status: 'unknown', url: '/api/trading/health' },
    { name: '策略平台', status: 'unknown', url: '/api/strategy/health' },
    { name: '通知服务', status: 'unknown', url: '/api/notification/health' },
  ]);
  const [loading, setLoading] = useState(false);
  const [analysisScores, setAnalysisScores] = useState<AnalysisScores>({
    technical: 0,
    fundamental: 0,
    sentiment: 0,
    risk: 0
  });
  const [loadingTechnical, setLoadingTechnical] = useState(false);
  const [loadingFundamental, setLoadingFundamental] = useState(false);
  const [loadingSentiment, setLoadingSentiment] = useState(false);
  const [loadingRisk, setLoadingRisk] = useState(false);

  // 自动化交易模块状态
  const [autoTradingStrategies, setAutoTradingStrategies] = useState(0);
  const [strategyAutomationTasks, setStrategyAutomationTasks] = useState(0);
  const [scheduledTasks, setScheduledTasks] = useState(0);
  const [autoReports, setAutoReports] = useState(0);
  const [loadingAutoTrading, setLoadingAutoTrading] = useState(false);
  const [loadingStrategyAutomation, setLoadingStrategyAutomation] = useState(false);
  const [loadingScheduledTasks, setLoadingScheduledTasks] = useState(false);
  const [loadingAutoReports, setLoadingAutoReports] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAuthenticated, logout } = useAuth();

  // 根据路径获取选中的菜单key
  const getSelectedMenuKey = (pathname: string): string => {
    // 移除末尾的斜杠并标准化路径
    const normalizedPath = pathname.replace(/\/$/, '') || '/';
    
    switch (normalizedPath) {
      case '/':
        return 'dashboard';
      case '/technical-analysis':
        return 'technical-analysis';
      case '/fundamental-analysis':
        return 'fundamental-analysis';
      case '/sentiment-analysis':
        return 'sentiment-analysis';
      case '/risk-analysis':
        return 'risk-analysis';
      case '/trading':
        return 'trading';
      case '/trading-management':
        return 'trading-management';
      case '/strategies':
        return 'strategies';
      case '/auto-trading':
        return 'auto-trading';
      case '/strategy-automation':
        return 'strategy-automation';
      case '/settings':
        return 'settings';
      case '/network-optimization':
        return 'network-optimization';
      case '/websocket-trading':
        return 'websocket-trading';
      default:
        // 如果没有精确匹配，尝试部分匹配
        if (normalizedPath.includes('risk-analysis')) return 'risk-analysis';
        if (normalizedPath.includes('technical-analysis')) return 'technical-analysis';
        if (normalizedPath.includes('fundamental-analysis')) return 'fundamental-analysis';
        if (normalizedPath.includes('sentiment-analysis')) return 'sentiment-analysis';
        if (normalizedPath.includes('trading')) return 'trading';
        if (normalizedPath.includes('account')) return 'account';
        if (normalizedPath.includes('strategies')) return 'strategies';
        if (normalizedPath.includes('settings')) return 'settings';
        return 'dashboard';
    }
  };

  useEffect(() => {
    checkServices();
    fetchAnalysisScores();
    const interval = setInterval(checkServices, 30000); // 每30秒检查一次
    return () => clearInterval(interval);
  }, []);

  const fetchAnalysisScores = async () => {
    if (!isAuthenticated) return;

    try {
      // 获取技术分析分数
      setLoadingTechnical(true);
      try {
        const technicalResponse = await fetch('/api/config/analysis/technical', {
          credentials: 'include'
        });
        if (technicalResponse.ok) {
          const technicalData = await technicalResponse.json();
          setAnalysisScores(prev => ({ ...prev, technical: technicalData.score || 0 }));
        }
      } catch (error) {
        console.warn('获取技术分析分数失败:', error);
      }
      setLoadingTechnical(false);

      // 获取基本面分析分数
      setLoadingFundamental(true);
      try {
        const fundamentalResponse = await fetch('/api/config/analysis/fundamental', {
          credentials: 'include'
        });
        if (fundamentalResponse.ok) {
          const fundamentalData = await fundamentalResponse.json();
          setAnalysisScores(prev => ({ ...prev, fundamental: fundamentalData.score || 0 }));
        }
      } catch (error) {
        console.warn('获取基本面分析分数失败:', error);
      }
      setLoadingFundamental(false);

      // 获取情绪分析分数
      setLoadingSentiment(true);
      try {
        const sentimentResponse = await fetch('/api/config/analysis/sentiment', {
          credentials: 'include'
        });
        if (sentimentResponse.ok) {
          const sentimentData = await sentimentResponse.json();
          setAnalysisScores(prev => ({ ...prev, sentiment: sentimentData.score || 0 }));
        }
      } catch (error) {
        console.warn('获取情绪分析分数失败:', error);
      }
      setLoadingSentiment(false);

      // 获取风险分析分数
      setLoadingRisk(true);
      try {
        const riskResponse = await fetch('/api/config/analysis/risk', {
          credentials: 'include'
        });
        if (riskResponse.ok) {
          const riskData = await riskResponse.json();
          setAnalysisScores(prev => ({ ...prev, risk: riskData.score || 0 }));
        }
      } catch (error) {
        console.warn('获取风险分析分数失败:', error);
      }
      setLoadingRisk(false);

      // 获取自动化交易数据
      setLoadingAutoTrading(true);
      try {
        const autoTradingResponse = await fetch('http://localhost:8003/api/strategies', {
          credentials: 'include'
        });
        if (autoTradingResponse.ok) {
          const autoTradingData = await autoTradingResponse.json();
          setAutoTradingStrategies(autoTradingData.count || 0);
        }
      } catch (error) {
        console.warn('获取自动化交易策略数失败:', error);
      }
      setLoadingAutoTrading(false);

      setLoadingStrategyAutomation(true);
      try {
        const strategyAutoResponse = await fetch('/api/config/analysis/fundamental', {
          credentials: 'include'
        });
        if (strategyAutoResponse.ok) {
          const strategyAutoData = await strategyAutoResponse.json();
          setStrategyAutomationTasks(strategyAutoData.score || 0);
        }
      } catch (error) {
        console.warn('获取策略自动化任务数失败:', error);
      }
      setLoadingStrategyAutomation(false);

      setLoadingScheduledTasks(true);
      try {
        const scheduledResponse = await fetch('/api/config/analysis/sentiment', {
          credentials: 'include'
        });
        if (scheduledResponse.ok) {
          const scheduledData = await scheduledResponse.json();
          setScheduledTasks(scheduledData.score || 0);
        }
      } catch (error) {
        console.warn('获取定时任务数失败:', error);
      }
      setLoadingScheduledTasks(false);

      setLoadingAutoReports(true);
      try {
        const reportsResponse = await fetch('/api/config/analysis/risk', {
          credentials: 'include'
        });
        if (reportsResponse.ok) {
          const reportsData = await reportsResponse.json();
          setAutoReports(reportsData.score || 0);
        }
      } catch (error) {
        console.warn('获取自动报告数失败:', error);
      }
      setLoadingAutoReports(false);
    } catch (error) {
      console.error('获取分析分数失败:', error);
    }
  };

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

  // 从分析分数中提取显示值
  const technicalAnalysisScore = analysisScores.technical;
  const fundamentalAnalysisScore = analysisScores.fundamental;
  const sentimentAnalysisScore = analysisScores.sentiment;
  const riskAnalysisScore = analysisScores.risk;

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
          selectedKeys={[getSelectedMenuKey(location.pathname)]}
          items={[
            {
              key: 'dashboard',
              icon: <DashboardOutlined />,
              label: '仪表板',
              onClick: () => navigate('/')
            },
            {
              key: 'technical-analysis',
              icon: <LineChartOutlined />,
              label: '技术分析',
              onClick: () => navigate('/technical-analysis')
            },
            {
              key: 'fundamental-analysis',
              icon: <BarChartOutlined />,
              label: '基本面分析',
              onClick: () => navigate('/fundamental-analysis')
            },
            {
              key: 'sentiment-analysis',
              icon: <PieChartOutlined />,
              label: '情绪分析',
              onClick: () => navigate('/sentiment-analysis')
            },
            {
              key: 'news',
              icon: <PieChartOutlined />,
              label: '新闻情绪',
              onClick: () => navigate('/news')
            },
            {
              key: 'risk-analysis',
              icon: <FundOutlined />,
              label: '风险分析',
              onClick: () => navigate('/risk-analysis')
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
              key: 'account',
              icon: <FundOutlined />,
              label: '账户总览',
              onClick: () => navigate('/account')
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
                        <Title level={4}>系统概览</Title>
                        <Row gutter={16}>
                          <Col span={6}>
                            <Statistic 
                              title="运行中服务" 
                              value={healthyServices} 
                              suffix={`/ ${totalServices}`}
                              valueStyle={{ color: healthyServices === totalServices ? '#3f8600' : '#cf1322' }}
                            />
                          </Col>
                          <Col span={6}>
                            <Statistic 
                              title="系统状态" 
                              value={healthyServices === totalServices ? '正常' : '异常'} 
                              valueStyle={{ color: healthyServices === totalServices ? '#3f8600' : '#cf1322' }}
                            />
                          </Col>
                          <Col span={6}>
                            <Statistic 
                              title="策略数量" 
                              value={24}
                              valueStyle={{ color: '#1890ff' }}
                            />
                          </Col>
                          <Col span={6}>
                            <Statistic 
                              title="今日交易" 
                              value={156}
                              valueStyle={{ color: '#722ed1' }}
                            />
                          </Col>
                        </Row>
                      </Card>
                    </Col>

                    <Col span={24}>
                      <Card>
                        <Title level={4}>高级分析模块</Title>
                        <Row gutter={[16, 16]}>
                          <Col span={6}>
                            <Card 
                              hoverable 
                              style={{ marginBottom: 16 }}
                              onClick={() => navigate('/technical-analysis')}
                            >
                              <Statistic
                                title="技术分析"
                                value={technicalAnalysisScore}
                                suffix="%"
                                valueStyle={{ color: '#1890ff' }}
                                loading={loadingTechnical}
                              />
                              <Paragraph type="secondary" style={{ marginTop: 8 }}>
                                MA、MACD、RSI、KDJ、布林带等专业技术指标
                              </Paragraph>
                            </Card>
                          </Col>
                          
                          <Col span={6}>
                            <Card 
                              hoverable 
                              style={{ marginBottom: 16 }}
                              onClick={() => navigate('/fundamental-analysis')}
                            >
                              <Statistic
                                title="基本面分析"
                                value={fundamentalAnalysisScore}
                                suffix="%"
                                valueStyle={{ color: '#52c41a' }}
                                loading={loadingFundamental}
                              />
                              <Paragraph type="secondary" style={{ marginTop: 8 }}>
                                PE、PB、ROE、负债率等基本面指标分析
                              </Paragraph>
                            </Card>
                          </Col>
                          
                          <Col span={6}>
                            <Card 
                              hoverable 
                              style={{ marginBottom: 16 }}
                              onClick={() => navigate('/sentiment-analysis')}
                            >
                              <Statistic
                                title="情绪分析"
                                value={sentimentAnalysisScore}
                                suffix="%"
                                valueStyle={{ color: '#faad14' }}
                                loading={loadingSentiment}
                              />
                              <Paragraph type="secondary" style={{ marginTop: 8 }}>
                                市场情绪、新闻情感、社交媒体分析
                              </Paragraph>
                            </Card>
                          </Col>
                          
                          <Col span={6}>
                            <Card 
                              hoverable 
                              style={{ marginBottom: 16 }}
                              onClick={() => navigate('/risk-analysis')}
                            >
                              <Statistic
                                title="风险分析"
                                value={riskAnalysisScore}
                                suffix="%"
                                valueStyle={{ color: '#f5222d' }}
                                loading={loadingRisk}
                              />
                              <Paragraph type="secondary" style={{ marginTop: 8 }}>
                                VaR、夏普比率、最大回撤等风险管理
                              </Paragraph>
                            </Card>
                          </Col>
                        </Row>
                      </Card>
                    </Col>

                    {services.map((service) => (
                      <Col span={6} key={service.name}>
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
                        <Title level={4}>自动化交易模块</Title>
                        <Row gutter={[16, 16]}>
                          <Col span={6}>
                            <Card hoverable>
                              <Statistic
                                title="自动交易"
                                value={autoTradingStrategies}
                                suffix="个策略"
                                valueStyle={{ color: '#722ed1' }}
                                loading={loadingAutoTrading}
                              />
                              <Paragraph type="secondary" style={{ marginTop: 8 }}>
                                24/7 自动化执行
                              </Paragraph>
                            </Card>
                          </Col>
                          
                          <Col span={6}>
                            <Card hoverable>
                              <Statistic
                                title="策略自动化"
                                value={strategyAutomationTasks}
                                suffix="个任务"
                                valueStyle={{ color: '#13c2c2' }}
                                loading={loadingStrategyAutomation}
                              />
                              <Paragraph type="secondary" style={{ marginTop: 8 }}>
                                智能调优和优化
                              </Paragraph>
                            </Card>
                          </Col>
                          
                          <Col span={6}>
                            <Card hoverable>
                              <Statistic
                                title="定时任务"
                                value={scheduledTasks}
                                suffix="个任务"
                                valueStyle={{ color: '#fa8c16' }}
                                loading={loadingScheduledTasks}
                              />
                              <Paragraph type="secondary" style={{ marginTop: 8 }}>
                                定时执行和监控
                              </Paragraph>
                            </Card>
                          </Col>
                          
                          <Col span={6}>
                            <Card hoverable>
                              <Statistic
                                title="自动报告"
                                value={autoReports}
                                suffix="份报告"
                                valueStyle={{ color: '#52c41a' }}
                                loading={loadingAutoReports}
                              />
                              <Paragraph type="secondary" style={{ marginTop: 8 }}>
                                定期生成分析报告
                              </Paragraph>
                            </Card>
                          </Col>
                        </Row>
                      </Card>
                    </Col>

                    <Col span={24}>
                      <Card>
                        <Title level={4}>欢迎使用 CashUp v2 量化交易平台</Title>
                        <Paragraph>
                          CashUp 是一个专业的量化交易平台，集成了策略开发、回测分析、实时交易、风险管理等全方位功能。
                          采用先进的微服务架构，支持多交易所对接，提供专业级的技术分析工具和自动化交易系统。
                        </Paragraph>
                        <Alert
                          message="系统信息"
                          description={`当前系统正在运行中，所有核心服务状态正常。欢迎回来，${user?.username || user?.full_name || '用户'}！
                          系统已全面升级至v2版本，包含高级分析模块、自动化交易系统和智能风险管理功能。`}
                          type="success"
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
            <Route path="/technical-analysis" element={
              <ProtectedRoute>
                <TechnicalAnalysisChart />
              </ProtectedRoute>
            } />
            <Route path="/fundamental-analysis" element={
              <ProtectedRoute>
                <FundamentalAnalysis />
              </ProtectedRoute>
            } />
            <Route path="/sentiment-analysis" element={
              <ProtectedRoute>
                <SentimentAnalysis />
              </ProtectedRoute>
            } />
            <Route path="/news" element={
              <ProtectedRoute>
                <NewsPage />
              </ProtectedRoute>
            } />
            <Route path="/risk-analysis" element={
              <ProtectedRoute>
                <RiskAnalysis />
              </ProtectedRoute>
            } />
            <Route path="/account" element={
              <ProtectedRoute>
                <AccountOverview />
              </ProtectedRoute>
            } />
            <Route path="/auto-trading" element={
              <ProtectedRoute>
                <AutoTradingInterface />
              </ProtectedRoute>
            } />
            <Route path="/strategy-automation" element={
              <ProtectedRoute>
                <StrategyAutomation />
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