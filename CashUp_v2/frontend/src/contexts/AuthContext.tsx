/**
 * 认证上下文 - 管理全局认证状态
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
/**
 * 函数集注释：
 * - AuthContext: 提供 user/isAuthenticated/loading 与 login/logout
 * - useAuth/useIsAuthenticated: 读取认证状态
 * - initializeAuth/clearAuthState/fetchUserInfo: 初始化与状态维护
 */
import { message } from 'antd';
import { authAPI, authAPIWithCookies, handleApiError } from '../services/api';

interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  isRefreshing: boolean;
  apiCallWithRetry: <T>(apiFunction: () => Promise<T>, maxRetries?: number) => Promise<T | null>;
  sessionTimeout: number;
  setSessionTimeout: (timeout: number) => void;
  updateLastActivity: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// 自定义Hook：检查是否已认证
export const useIsAuthenticated = () => {
  const { isAuthenticated, loading } = useAuth();
  return { isAuthenticated, loading };
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastActivity, setLastActivity] = useState<number>(Date.now());
  const [sessionTimeout, setSessionTimeout] = useState<number>(30 * 60 * 1000); // 30分钟超时

  // 初始化认证状态
  useEffect(() => {
    const initializeAuth = async () => {
      setLoading(true);
      if (!AUTH_ENABLED) {
        const defaultUser: User = {
          id: 'dev',
          username: 'developer',
          email: 'dev@local',
          full_name: '开发模式',
          role: 'admin',
        };
        setUser(defaultUser);
        setIsAuthenticated(true);
        setLoading(false);
        return;
      }
      const token = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');
      
      if (token) {
        try {
          // 首先尝试直接获取用户信息
          await fetchUserInfo();
        } catch (error) {
          // 如果直接获取失败，尝试使用refresh token
          if (refreshToken) {
            try {
              const refreshSuccess = await refreshTokenFunc();
              if (!refreshSuccess) {
                // Token刷新失败，清除认证状态
                clearAuthState();
              }
            } catch (refreshError) {
              // Refresh token也失败，清除认证状态
              clearAuthState();
            }
          } else {
            // 没有refresh token，直接清除认证状态
            clearAuthState();
          }
        }
      } else {
        // 没有token，确保认证状态为false
        clearAuthState();
      }
      
      setLoading(false);
    };

    initializeAuth();
  }, []);

  // 清除认证状态的辅助函数
  const clearAuthState = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
    setIsAuthenticated(false);
  };

  // 自动刷新用户信息
  useEffect(() => {
    if (isAuthenticated && AUTH_ENABLED) {
      const interval = setInterval(async () => {
        try {
          // 首先尝试直接获取用户信息
          await fetchUserInfo();
        } catch (error) {
          // 如果直接获取失败，尝试使用refresh token
          const refreshSuccess = await refreshTokenFunc();
          if (!refreshSuccess) {
            // Token刷新失败，清除认证状态
            clearAuthState();
          }
        }
      }, 300000); // 每5分钟刷新一次
      
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  // 会话超时检查
  useEffect(() => {
    if (isAuthenticated && AUTH_ENABLED) {
      const timeoutCheck = setInterval(() => {
        const now = Date.now();
        const timeSinceLastActivity = now - lastActivity;
        
        if (timeSinceLastActivity > sessionTimeout) {
          console.log('会话超时，自动登出');
          clearAuthState();
          message.warning('会话已超时，请重新登录');
        }
      }, 60000); // 每分钟检查一次
      
      return () => clearInterval(timeoutCheck);
    }
  }, [isAuthenticated, lastActivity, sessionTimeout]);

  // 更新最后活动时间的函数
  const updateLastActivity = () => {
    setLastActivity(Date.now());
  };

  // 监听用户活动事件
  useEffect(() => {
    if (isAuthenticated) {
      const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
      
      const handleActivity = () => {
        updateLastActivity();
      };
      
      activityEvents.forEach(event => {
        window.addEventListener(event, handleActivity);
      });
      
      return () => {
        activityEvents.forEach(event => {
          window.removeEventListener(event, handleActivity);
        });
      };
    }
  }, [isAuthenticated]);

  const fetchUserInfo = async () => {
    try {
      // 使用Cookie认证API获取用户信息
      const response = await authAPIWithCookies.getCurrentUser();
      if (response) {
        setUser(response as unknown as User);
        setIsAuthenticated(true);
      }
    } catch (error) {
      console.error('获取用户信息失败:', error);
      throw error;
    }
  };

  // Token刷新机制
  const refreshTokenFunc = async (): Promise<boolean> => {
    try {
      setIsRefreshing(true);
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        throw new Error('No token found');
      }

      // 尝试使用refresh token刷新token
      const storedRefreshToken = localStorage.getItem('refresh_token');
      
      if (storedRefreshToken) {
        try {
          // 调用刷新token的API
          const response = await authAPI.refreshToken(storedRefreshToken);
          
          if (response && (response as any).access_token) {
            localStorage.setItem('access_token', (response as any).access_token);
            if ((response as any).refresh_token) {
              localStorage.setItem('refresh_token', (response as any).refresh_token);
            }
            
            // 重新获取用户信息
            await fetchUserInfo();
            return true;
          }
        } catch (refreshError) {
          console.warn('Refresh token失效，尝试使用现有token获取用户信息');
        }
      }

      // 如果没有storedRefresh token或refresh失败，尝试直接获取用户信息
      await fetchUserInfo();
      return true;
    } catch (error) {
      console.error('Token刷新失败:', error);
      // 清除所有认证相关的存储
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      setUser(null);
      setIsAuthenticated(false);
      return false;
    } finally {
      setIsRefreshing(false);
    }
  };

  const refreshUser = async () => {
    try {
      await fetchUserInfo();
    } catch (error) {
      const errorMessage = handleApiError(error);
      console.error('刷新用户信息失败:', error);
      throw new Error(errorMessage);
    }
  };

  // 带Token重试的API调用包装器
  const apiCallWithRetry = async <T extends any>(
    apiFunction: () => Promise<T>,
    maxRetries: number = 1
  ): Promise<T | null> => {
    try {
      const result = await apiFunction();
      return result;
    } catch (error: any) {
      // 如果是401错误且还有重试次数，尝试刷新token
      if (error.response?.status === 401 && maxRetries > 0) {
        const refreshSuccess = await refreshTokenFunc();
        if (refreshSuccess) {
          return apiCallWithRetry(apiFunction, maxRetries - 1);
        }
      }
      throw error;
    }
  };

  const login = async (username: string, password: string) => {
    setLoading(true);
    try {
      // 使用Cookie认证API
      const response = await authAPIWithCookies.login(username, password);
      
      if (response) {
        // 根据API响应处理token
        const accessToken = (response as any).access_token || (response as any).session_id;
        const refreshToken = (response as any).refresh_token;
        
        if (accessToken) {
          localStorage.setItem('access_token', accessToken);
        }
        
        if (refreshToken) {
          localStorage.setItem('refresh_token', refreshToken);
        }
        
        // 设置用户信息和认证状态
        if ((response as any).user) {
          setUser((response as any).user);
        } else {
          // 如果没有用户信息，获取当前用户信息
          try {
            const userResponse = await authAPIWithCookies.getCurrentUser();
            if (userResponse) {
              setUser(userResponse as unknown as User);
            } else {
              // 如果没有用户信息，默认设置
              const defaultUser: User = {
                id: '1',
                username: username,
                email: 'admin@cashup.com',
                full_name: '系统管理员',
                role: 'admin'
              };
              setUser(defaultUser);
            }
          } catch (userError) {
            console.warn('获取用户信息失败，使用默认信息:', userError);
            const defaultUser: User = {
              id: '1',
              username: username,
              email: 'admin@cashup.com',
              full_name: '系统管理员',
              role: 'admin'
            };
            setUser(defaultUser);
          }
        }
        
        setIsAuthenticated(true);
        
        // 确保状态更新完成
        await new Promise(resolve => setTimeout(resolve, 100));
      }
    } catch (error) {
      const errorMessage = handleApiError(error);
      console.error('登录失败:', error);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      // 调用后端登出API清除Cookie
      await authAPIWithCookies.logout();
    } catch (error) {
      console.warn('登出API调用失败:', error);
    } finally {
      clearAuthState();
    }
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      loading, 
      isAuthenticated, 
      login, 
      logout, 
      refreshUser,
      isRefreshing,
      apiCallWithRetry,
      sessionTimeout,
      setSessionTimeout,
      updateLastActivity
    }}>
      {children}
    </AuthContext.Provider>
  );
};
const AUTH_ENABLED = (window.ENV?.REACT_APP_ENABLE_AUTH ?? 'true') === 'true';