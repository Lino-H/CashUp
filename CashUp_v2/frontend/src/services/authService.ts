/**
 * 认证服务 - 简化版（基于会话）
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  role: string;
  status: string;
  is_verified: boolean;
  avatar_url?: string;
  last_login?: string;
  created_at: string;
}

export interface LoginResponse {
  session_id: string;
  user: User;
}

class AuthService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/api/auth`;
  }

  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await fetch(`${this.baseUrl}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
      credentials: 'include', // 包含cookies
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '登录失败');
    }

    return response.json();
  }

  async register(userData: RegisterRequest): Promise<User> {
    const response = await fetch(`${this.baseUrl}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '注册失败');
    }

    return response.json();
  }

  async logout(): Promise<void> {
    const response = await fetch(`${this.baseUrl}/logout`, {
      method: 'POST',
      credentials: 'include', // 包含cookies
    });

    if (!response.ok) {
      throw new Error('登出失败');
    }
  }

  async getCurrentUser(): Promise<User | null> {
    try {
      const response = await fetch(`${this.baseUrl}/me`, {
        method: 'GET',
        credentials: 'include', // 包含cookies
      });

      if (!response.ok) {
        if (response.status === 401) {
          return null; // 未登录
        }
        throw new Error('获取用户信息失败');
      }

      return response.json();
    } catch (error) {
      console.error('获取用户信息失败:', error);
      return null;
    }
  }

  async isAuthenticated(): Promise<boolean> {
    const user = await this.getCurrentUser();
    return user !== null;
  }

  // 获取session_id（用于API调用）
  getSessionId(): string | null {
    const cookies = document.cookie.split(';');
    for (const cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === 'session_id') {
        return value;
      }
    }
    return null;
  }

  // 获取认证头（用于API调用）
  getAuthHeaders(): Record<string, string> {
    const sessionId = this.getSessionId();
    return sessionId ? 
      { 'Authorization': `Bearer ${sessionId}` } : 
      {};
  }
}

export const authService = new AuthService();
export default authService;