import React from 'react'
import { createBrowserRouter, Navigate } from 'react-router-dom'
import App from '../App'
import Login from '../pages/Login'
import Dashboard from '../pages/Dashboard'
import StrategyManagement from '../pages/StrategyManagement'
import TradingMonitor from '../pages/TradingMonitor'
import MarketAnalysis from '../pages/MarketAnalysis'
import RiskManagement from '../pages/RiskManagement'
import NotificationCenter from '../pages/NotificationCenter'
import SystemSettings from '../pages/SystemSettings'
import { AuthProvider, useAuth } from '../contexts/AuthContext'

// 路由守卫组件
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth()
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold">Loading...</h1>
        </div>
      </div>
    )
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

// 公共路由组件（已登录用户重定向到仪表板）
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth()
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold">Loading...</h1>
        </div>
      </div>
    )
  }
  
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }
  
  return <>{children}</>
}

// 路由配置
export const router = createBrowserRouter([
  {
    path: '/login',
    element: (
      <AuthProvider>
        <PublicRoute>
          <Login />
        </PublicRoute>
      </AuthProvider>
    )
  },
  {
    path: '/',
    element: (
      <AuthProvider>
        <ProtectedRoute>
          <App />
        </ProtectedRoute>
      </AuthProvider>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />
      },
      {
        path: 'dashboard',
        element: <Dashboard />
      },
      {
        path: 'strategies',
        element: <StrategyManagement />
      },
      {
        path: 'trading',
        element: <TradingMonitor />
      },
      {
        path: 'market',
        element: <MarketAnalysis />
      },
      {
        path: 'risk',
        element: <RiskManagement />
      },
      {
        path: 'notifications',
        element: <NotificationCenter />
      },
      {
        path: 'settings',
        element: <SystemSettings />
      }
    ]
  },
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />
  }
])

export default router