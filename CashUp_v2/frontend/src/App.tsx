/**
 * 主应用组件 - 集成认证
 * Main Application Component with Authentication
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout, Menu, Button, Spin } from 'antd';
import {
  DashboardOutlined,
  BarChartOutlined,
  TradingOutlined,
  AccountBookOutlined,
  LineChartOutlined,
  SettingOutlined,
  LogoutOutlined
} from '@ant-design/icons';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import StrategyManagement from './pages/StrategyManagement';
import BacktestResults from './pages/BacktestResults';
import RealTimeTrading from './pages/RealTimeTrading';
import DataAnalysis from './pages/DataAnalysis';
import UserSettings from './pages/UserSettings';
import LoginPage from './pages/LoginPage';

const { Header, Sider, Content } = Layout;

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

const MainLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const [collapsed, setCollapsed] = React.useState(false);

  const menuItems = [
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: '仪表板',
      path: '/dashboard'
    },
    {
      key: 'strategies',
      icon: <BarChartOutlined />,
      label: '策略管理',
      path: '/strategies'
    },
    {
      key: 'backtest',
      icon: <LineChartOutlined />,
      label: '回测分析',
      path: '/backtest'
    },
    {
      key: 'trading',
      icon: <TradingOutlined />,
      label: '实时交易',
      path: '/trading'
    },
    {
      key: 'portfolio',
      icon: <AccountBookOutlined />,
      label: '账户管理',
      path: '/portfolio'
    },
    {
      key: 'analytics',
      icon: <BarChartOutlined />,
      label: '数据分析',
      path: '/analytics'
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '系统设置',
      path: '/settings'
    }
  ];

  const handleLogout = async () => {
    await logout();
  };

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
          defaultSelectedKeys={['strategies']}
          items={menuItems.map(item => ({
            key: item.key,
            icon: item.icon,
            label: item.label,
            onClick: () => {
              // 简单的路由导航
              window.location.hash = item.path;
            }
          }))}
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
            <h1 style={{ margin: 0, fontSize: 20, color: '#001529' }}>
              CashUp 量化交易平台
            </h1>
          </div>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <span style={{ marginRight: 16 }}>
              欢迎回来，{user?.full_name || user?.username || '用户'}
            </span>
            <Button 
              type="primary" 
              icon={<LogoutOutlined />}
              onClick={handleLogout}
              size="small"
            >
              退出
            </Button>
          </div>
        </Header>
        <Content style={{ margin: '24px 16px', padding: 24, background: '#fff' }}>
          <Routes>
            <Route path="/" element={<Navigate to="/strategies" replace />} />
            <Route path="/strategies" element={<StrategyManagement />} />
            <Route path="/backtest" element={<BacktestResults />} />
            <Route path="/trading" element={<RealTimeTrading />} />
            <Route path="/portfolio" element={<div>账户管理页面（开发中）</div>} />
            <Route path="/analytics" element={<DataAnalysis />} />
            <Route path="/settings" element={<UserSettings />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/*" element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          } />
        </Routes>
      </Router>
    </AuthProvider>
  );
};

export default App;