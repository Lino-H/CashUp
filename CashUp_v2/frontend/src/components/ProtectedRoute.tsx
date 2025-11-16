import React, { memo } from 'react';
/**
 * 函数集注释：
 * - ProtectedRoute: 在启用认证时阻止未登录用户访问受保护路由
 */
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = memo(({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  const AUTH_ENABLED = (window.ENV?.REACT_APP_ENABLE_AUTH ?? 'true') === 'true';

  if (AUTH_ENABLED && loading) {
    return <div>Loading...</div>;
  }

  if (AUTH_ENABLED && !isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
});

ProtectedRoute.displayName = 'ProtectedRoute';