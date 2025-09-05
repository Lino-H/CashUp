/**
 * 用户设置API服务
 * User Settings API Service
 */

import { message } from 'antd';

// 用户配置类型
export interface UserConfig {
  id: string;
  username: string;
  email: string;
  phone?: string;
  avatar?: string;
  timezone: string;
  language: string;
  theme: 'light' | 'dark' | 'auto';
  notifications: {
    email: boolean;
    push: boolean;
    sms: boolean;
    tradeAlerts: boolean;
    riskAlerts: boolean;
    systemAlerts: boolean;
    marketing: boolean;
  };
  security: {
    twoFactorEnabled: boolean;
    loginAlerts: boolean;
    sessionTimeout: number;
    passwordPolicy: {
      minLength: number;
      requireUppercase: boolean;
      requireNumbers: boolean;
      requireSpecialChars: boolean;
      expireDays: number;
    };
  };
  trading: {
    defaultExchange: string;
    defaultLeverage: number;
    riskPerTrade: number;
    maxDailyLoss: number;
    maxPositions: number;
    autoStopLoss: boolean;
    autoTakeProfit: boolean;
    slippageTolerance: number;
  };
  api: {
    enabled: boolean;
    rateLimit: number;
    ipWhitelist: string[];
    webhooks: Array<{
      id: string;
      url: string;
      events: string[];
      active: boolean;
    }>;
  };
  data: {
    autoBackup: boolean;
    backupFrequency: 'daily' | 'weekly' | 'monthly';
    retentionPeriod: number;
    exportFormat: 'csv' | 'json' | 'excel';
  };
}

// 交易所配置类型
export interface ExchangeConfig {
  id: string;
  name: string;
  type: string;
  apiKey: string;
  apiSecret: string;
  passphrase?: string;
  enabled: boolean;
  testnet: boolean;
  rateLimits: {
    requests: number;
    window: string;
  };
  features: {
    spot: boolean;
    margin: boolean;
    futures: boolean;
    tradingBot: boolean;
  };
  lastSync?: string;
  status: 'connected' | 'disconnected' | 'error';
}

// 系统配置类型
export interface SystemConfig {
  version: string;
  build: string;
  environment: 'development' | 'staging' | 'production';
  database: {
    type: string;
    version: string;
    size: string;
    connections: number;
  };
  redis: {
    version: string;
    memory: string;
    connections: number;
  };
  services: Array<{
    name: string;
    status: 'running' | 'stopped' | 'error';
    cpu: number;
    memory: number;
    uptime: string;
  }>;
}

// API密钥类型
export interface ApiKey {
  id: string;
  name: string;
  key: string;
  secret: string;
  permissions: string[];
  ipWhitelist: string[];
  rateLimit: number;
  createdAt: string;
  expiresAt?: string;
  lastUsed?: string;
  active: boolean;
}

// Webhook配置类型
export interface WebhookConfig {
  id: string;
  name: string;
  url: string;
  events: string[];
  headers: Record<string, string>;
  active: boolean;
  retries: number;
  timeout: number;
  createdAt: string;
  lastTriggered?: string;
  successCount: number;
  failureCount: number;
}

// 活动日志类型
export interface ActivityLog {
  id: string;
  userId: string;
  action: string;
  resource: string;
  resourceId?: string;
  details: Record<string, any>;
  ipAddress: string;
  userAgent: string;
  timestamp: string;
  status: 'success' | 'failed';
}

// 数据备份类型
export interface DataBackup {
  id: string;
  name: string;
  type: 'manual' | 'scheduled';
  size: string;
  status: 'pending' | 'completed' | 'failed';
  createdAt: string;
  expiresAt?: string;
  downloadUrl?: string;
}

// 密码重置类型
export interface PasswordReset {
  token: string;
  newPassword: string;
  confirmPassword: string;
}

// 2FA验证类型
export interface TwoFactorSetup {
  secret: string;
  qrCodeUrl: string;
  backupCodes: string[];
}

// 用户偏好类型
export interface UserPreferences {
  dashboard: {
    layout: 'default' | 'compact' | 'detailed';
    widgets: string[];
    refreshInterval: number;
  };
  charts: {
    defaultTheme: 'light' | 'dark';
    defaultType: 'line' | 'candlestick' | 'bar';
    showVolume: boolean;
    showIndicators: boolean;
  };
  trading: {
    confirmOrder: boolean;
    showAdvancedOptions: boolean;
    defaultOrderType: 'market' | 'limit';
  };
}

class UserSettingsService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8001';
  }

  // 获取用户配置
  async getUserConfig(): Promise<UserConfig> {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/config`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取用户配置失败:', error);
      throw error;
    }
  }

  // 更新用户配置
  async updateUserConfig(config: Partial<UserConfig>): Promise<UserConfig> {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/config`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      message.success('配置更新成功');
      return result;
    } catch (error) {
      console.error('更新用户配置失败:', error);
      message.error('配置更新失败');
      throw error;
    }
  }

  // 修改密码
  async changePassword(data: {
    currentPassword: string;
    newPassword: string;
    confirmPassword: string;
  }): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      message.success('密码修改成功');
    } catch (error) {
      console.error('修改密码失败:', error);
      message.error('密码修改失败');
      throw error;
    }
  }

  // 启用两步验证
  async enable2FA(): Promise<TwoFactorSetup> {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/2fa/enable`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('启用2FA失败:', error);
      message.error('启用2FA失败');
      throw error;
    }
  }

  // 验证并完成2FA设置
  async verify2FA(data: {
    token: string;
    backupCode?: string;
  }): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/2fa/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      message.success('2FA设置成功');
    } catch (error) {
      console.error('验证2FA失败:', error);
      message.error('验证2FA失败');
      throw error;
    }
  }

  // 禁用两步验证
  async disable2FA(data: {
    token: string;
    password: string;
  }): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/2fa/disable`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      message.success('2FA已禁用');
    } catch (error) {
      console.error('禁用2FA失败:', error);
      message.error('禁用2FA失败');
      throw error;
    }
  }

  // 获取交易所配置
  async getExchangeConfigs(): Promise<ExchangeConfig[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/exchanges`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取交易所配置失败:', error);
      throw error;
    }
  }

  // 添加交易所配置
  async addExchangeConfig(config: Omit<ExchangeConfig, 'id' | 'status' | 'lastSync'>): Promise<ExchangeConfig> {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/exchanges`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      message.success('交易所配置添加成功');
      return result;
    } catch (error) {
      console.error('添加交易所配置失败:', error);
      message.error('添加交易所配置失败');
      throw error;
    }
  }

  // 更新交易所配置
  async updateExchangeConfig(id: string, config: Partial<ExchangeConfig>): Promise<ExchangeConfig> {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/exchanges/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      message.success('交易所配置更新成功');
      return result;
    } catch (error) {
      console.error('更新交易所配置失败:', error);
      message.error('更新交易所配置失败');
      throw error;
    }
  }

  // 删除交易所配置
  async deleteExchangeConfig(id: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/exchanges/${id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      message.success('交易所配置删除成功');
    } catch (error) {
      console.error('删除交易所配置失败:', error);
      message.error('删除交易所配置失败');
      throw error;
    }
  }

  // 测试交易所连接
  async testExchangeConnection(id: string): Promise<{
    status: 'success' | 'error';
    message: string;
    latency?: number;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/exchanges/${id}/test`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('测试交易所连接失败:', error);
      throw error;
    }
  }

  // 获取API密钥
  async getApiKeys(): Promise<ApiKey[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/api-keys`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取API密钥失败:', error);
      throw error;
    }
  }

  // 创建API密钥
  async createApiKey(data: {
    name: string;
    permissions: string[];
    ipWhitelist: string[];
    rateLimit: number;
    expiresAt?: string;
  }): Promise<{ apiKey: ApiKey; secret: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/api-keys`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      message.success('API密钥创建成功');
      return result;
    } catch (error) {
      console.error('创建API密钥失败:', error);
      message.error('创建API密钥失败');
      throw error;
    }
  }

  // 删除API密钥
  async deleteApiKey(id: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/api-keys/${id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      message.success('API密钥删除成功');
    } catch (error) {
      console.error('删除API密钥失败:', error);
      message.error('删除API密钥失败');
      throw error;
    }
  }

  // 获取Webhook配置
  async getWebhooks(): Promise<WebhookConfig[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/webhooks`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取Webhook配置失败:', error);
      throw error;
    }
  }

  // 创建Webhook配置
  async createWebhook(config: Omit<WebhookConfig, 'id' | 'createdAt' | 'lastTriggered' | 'successCount' | 'failureCount'>): Promise<WebhookConfig> {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/webhooks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      message.success('Webhook配置创建成功');
      return result;
    } catch (error) {
      console.error('创建Webhook配置失败:', error);
      message.error('创建Webhook配置失败');
      throw error;
    }
  }

  // 测试Webhook
  async testWebhook(id: string): Promise<{
    status: 'success' | 'error';
    message: string;
    response?: any;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/webhooks/${id}/test`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('测试Webhook失败:', error);
      throw error;
    }
  }

  // 获取活动日志
  async getActivityLogs(params?: {
    page?: number;
    limit?: number;
    action?: string;
    resource?: string;
    startDate?: string;
    endDate?: string;
  }): Promise<{
    logs: ActivityLog[];
    total: number;
    page: number;
    limit: number;
  }> {
    try {
      const queryString = params ? `?${new URLSearchParams(params as any).toString()}` : '';
      const response = await fetch(`${this.baseUrl}/api/user/activity-logs${queryString}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取活动日志失败:', error);
      throw error;
    }
  }

  // 获取数据备份
  async getDataBackups(): Promise<DataBackup[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/backups`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取数据备份失败:', error);
      throw error;
    }
  }

  // 创建数据备份
  async createBackup(data: {
    name: string;
    includeData: string[];
  }): Promise<DataBackup> {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/backups`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      message.success('数据备份创建成功');
      return result;
    } catch (error) {
      console.error('创建数据备份失败:', error);
      message.error('创建数据备份失败');
      throw error;
    }
  }

  // 恢复数据备份
  async restoreBackup(id: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/backups/${id}/restore`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      message.success('数据恢复成功');
    } catch (error) {
      console.error('恢复数据备份失败:', error);
      message.error('恢复数据备份失败');
      throw error;
    }
  }

  // 导出用户数据
  async exportUserData(params: {
    format: 'csv' | 'json' | 'excel';
    includeData: string[];
  }): Promise<{ downloadUrl: string; filename: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/export`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('导出用户数据失败:', error);
      throw error;
    }
  }

  // 导入用户数据
  async importUserData(data: {
    file: File;
    mergeStrategy: 'replace' | 'merge' | 'skip';
  }): Promise<void> {
    try {
      const formData = new FormData();
      formData.append('file', data.file);
      formData.append('mergeStrategy', data.mergeStrategy);

      const response = await fetch(`${this.baseUrl}/api/user/import`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      message.success('用户数据导入成功');
    } catch (error) {
      console.error('导入用户数据失败:', error);
      message.error('导入用户数据失败');
      throw error;
    }
  }

  // 获取系统配置
  async getSystemConfig(): Promise<SystemConfig> {
    try {
      const response = await fetch(`${this.baseUrl}/api/system/config`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取系统配置失败:', error);
      throw error;
    }
  }

  // 获取用户偏好
  async getUserPreferences(): Promise<UserPreferences> {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/preferences`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取用户偏好失败:', error);
      throw error;
    }
  }

  // 更新用户偏好
  async updateUserPreferences(preferences: Partial<UserPreferences>): Promise<UserPreferences> {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/preferences`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(preferences),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('更新用户偏好失败:', error);
      throw error;
    }
  }

  // 删除用户账户
  async deleteAccount(data: {
    password: string;
    confirmationToken: string;
    reason?: string;
  }): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/user/account`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      message.success('账户删除成功');
    } catch (error) {
      console.error('删除账户失败:', error);
      message.error('删除账户失败');
      throw error;
    }
  }
}

// 创建单例实例
export const userSettingsService = new UserSettingsService();

// 导出类型
export type {
  UserConfig,
  ExchangeConfig,
  SystemConfig,
  ApiKey,
  WebhookConfig,
  ActivityLog,
  DataBackup,
  PasswordReset,
  TwoFactorSetup,
  UserPreferences
};