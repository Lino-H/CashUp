/**
 * 用户设置和配置测试
 * User Settings and Configuration Test
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import UserSettings from '../pages/UserSettings';
import { userSettingsService } from '../services/userSettingsService';

// Mock the user settings service
jest.mock('../services/userSettingsService');

const mockUserConfig = {
  id: '1',
  username: 'trader_user',
  email: 'trader@example.com',
  phone: '+86 138 0000 0000',
  avatar: '',
  timezone: 'Asia/Shanghai',
  language: 'zh-CN',
  theme: 'light' as const,
  notifications: {
    email: true,
    push: true,
    sms: false,
    tradeAlerts: true,
    riskAlerts: true,
    systemAlerts: true,
    marketing: false
  },
  security: {
    twoFactorEnabled: true,
    loginAlerts: true,
    sessionTimeout: 3600,
    passwordPolicy: {
      minLength: 8,
      requireUppercase: true,
      requireNumbers: true,
      requireSpecialChars: true,
      expireDays: 90
    }
  },
  trading: {
    defaultExchange: 'binance',
    defaultLeverage: 1,
    riskPerTrade: 2,
    maxDailyLoss: 5,
    maxPositions: 10,
    autoStopLoss: true,
    autoTakeProfit: true,
    slippageTolerance: 0.5
  },
  api: {
    enabled: false,
    rateLimit: 1000,
    ipWhitelist: ['127.0.0.1'],
    webhooks: []
  },
  data: {
    autoBackup: true,
    backupFrequency: 'daily' as const,
    retentionPeriod: 30,
    exportFormat: 'csv' as const
  }
};

const mockExchangeConfigs = [
  {
    id: '1',
    name: 'Binance',
    type: 'binance',
    apiKey: '********',
    apiSecret: '********',
    enabled: true,
    testnet: false,
    rateLimits: {
      requests: 1200,
      window: '1m'
    },
    features: {
      spot: true,
      margin: true,
      futures: true,
      tradingBot: true
    },
    lastSync: '2024-01-15T10:30:00Z',
    status: 'connected' as const
  },
  {
    id: '2',
    name: 'Gate.io',
    type: 'gateio',
    apiKey: '********',
    apiSecret: '********',
    enabled: true,
    testnet: false,
    rateLimits: {
      requests: 100,
      window: '1s'
    },
    features: {
      spot: true,
      margin: true,
      futures: false,
      tradingBot: true
    },
    lastSync: '2024-01-15T10:25:00Z',
    status: 'connected' as const
  }
];

const mockSystemConfig = {
  version: '2.0.0',
  build: '2024.01.15',
  environment: 'production' as const,
  database: {
    type: 'PostgreSQL',
    version: '15.4',
    size: '2.3 GB',
    connections: 45
  },
  redis: {
    version: '7.2',
    memory: '512 MB',
    connections: 12
  },
  services: [
    {
      name: 'core-service',
      status: 'running' as const,
      cpu: 15.2,
      memory: 256,
      uptime: '15d 4h 32m'
    },
    {
      name: 'trading-engine',
      status: 'running' as const,
      cpu: 25.8,
      memory: 512,
      uptime: '15d 4h 32m'
    },
    {
      name: 'strategy-platform',
      status: 'running' as const,
      cpu: 18.5,
      memory: 384,
      uptime: '15d 4h 32m'
    },
    {
      name: 'notification-service',
      status: 'running' as const,
      cpu: 8.3,
      memory: 128,
      uptime: '15d 4h 32m'
    }
  ]
};

describe('UserSettings Component', () => {
  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();
    
    // Mock the service methods
    (userSettingsService.getUserConfig as jest.Mock).mockResolvedValue(mockUserConfig);
    (userSettingsService.getExchangeConfigs as jest.Mock).mockResolvedValue(mockExchangeConfigs);
    (userSettingsService.getSystemConfig as jest.Mock).mockResolvedValue(mockSystemConfig);
    (userSettingsService.updateUserConfig as jest.Mock).mockResolvedValue(mockUserConfig);
    (userSettingsService.changePassword as jest.Mock).mockResolvedValue(undefined);
    (userSettingsService.enable2FA as jest.Mock).mockResolvedValue({
      secret: 'JBSWY3DPEHPK3PXP',
      qrCodeUrl: 'otpauth://totp/CashUp:trader_user?secret=JBSWY3DPEHPK3PXP&issuer=CashUp',
      backupCodes: ['ABC123', 'DEF456', 'GHI789']
    });
    (userSettingsService.verify2FA as jest.Mock).mockResolvedValue(undefined);
    (userSettingsService.disable2FA as jest.Mock).mockResolvedValue(undefined);
    (userSettingsService.testExchangeConnection as jest.Mock).mockResolvedValue({
      status: 'success',
      message: '连接成功',
      latency: 150
    });
    (userSettingsService.exportUserData as jest.Mock).mockResolvedValue({
      downloadUrl: '/api/exports/user-data.csv',
      filename: 'user-data.csv'
    });
  });

  test('renders user settings page correctly', async () => {
    render(
      <MemoryRouter>
        <UserSettings />
      </MemoryRouter>
    );

    // Check if the title is rendered
    expect(screen.getByText('用户设置和配置')).toBeInTheDocument();
    expect(screen.getByText('管理您的个人资料、安全设置、交易偏好和系统配置')).toBeInTheDocument();

    // Check if tabs are rendered
    expect(screen.getByText('个人资料')).toBeInTheDocument();
    expect(screen.getByText('安全设置')).toBeInTheDocument();
    expect(screen.getByText('通知设置')).toBeInTheDocument();
    expect(screen.getByText('交易设置')).toBeInTheDocument();
    expect(screen.getByText('交易所配置')).toBeInTheDocument();
    expect(screen.getByText('API设置')).toBeInTheDocument();
    expect(screen.getByText('数据管理')).toBeInTheDocument();
    expect(screen.getByText('系统设置')).toBeInTheDocument();
  });

  test('displays profile settings correctly', async () => {
    render(
      <MemoryRouter>
        <UserSettings />
      </MemoryRouter>
    );

    // Switch to profile tab
    fireEvent.click(screen.getByText('个人资料'));

    // Check if profile form is displayed
    await waitFor(() => {
      expect(screen.getByLabelText('用户名')).toBeInTheDocument();
      expect(screen.getByLabelText('邮箱')).toBeInTheDocument();
      expect(screen.getByLabelText('手机号')).toBeInTheDocument();
      expect(screen.getByLabelText('时区')).toBeInTheDocument();
      expect(screen.getByLabelText('语言')).toBeInTheDocument();
      expect(screen.getByLabelText('主题')).toBeInTheDocument();
    });

    // Check if default values are set
    await waitFor(() => {
      expect(screen.getByDisplayValue('trader_user')).toBeInTheDocument();
      expect(screen.getByDisplayValue('trader@example.com')).toBeInTheDocument();
      expect(screen.getByDisplayValue('+86 138 0000 0000')).toBeInTheDocument();
    });
  });

  test('handles profile settings save', async () => {
    render(
      <MemoryRouter>
        <UserSettings />
      </MemoryRouter>
    );

    // Switch to profile tab
    fireEvent.click(screen.getByText('个人资料'));

    // Wait for form to load
    await waitFor(() => {
      expect(screen.getByLabelText('用户名')).toBeInTheDocument();
    });

    // Modify form values
    fireEvent.change(screen.getByLabelText('用户名'), { target: { value: 'new_trader_user' } });
    fireEvent.change(screen.getByLabelText('邮箱'), { target: { value: 'new_trader@example.com' } });

    // Click save button
    fireEvent.click(screen.getByText('保存设置'));

    // Check if service was called
    await waitFor(() => {
      expect(userSettingsService.updateUserConfig).toHaveBeenCalled();
    });
  });

  test('displays security settings correctly', async () => {
    render(
      <MemoryRouter>
        <UserSettings />
      </MemoryRouter>
    );

    // Switch to security tab
    fireEvent.click(screen.getByText('安全设置'));

    // Check if security settings are displayed
    await waitFor(() => {
      expect(screen.getByText('密码设置')).toBeInTheDocument();
      expect(screen.getByText('两步验证')).toBeInTheDocument();
      expect(screen.getByText('登录安全')).toBeInTheDocument();
    });

    // Check if password form is displayed
    expect(screen.getByLabelText('当前密码')).toBeInTheDocument();
    expect(screen.getByLabelText('新密码')).toBeInTheDocument();
    expect(screen.getByLabelText('确认密码')).toBeInTheDocument();

    // Check if 2FA status is displayed
    expect(screen.getByText('两步验证已启用')).toBeInTheDocument();
  });

  test('handles password change', async () => {
    render(
      <MemoryRouter>
        <UserSettings />
      </MemoryRouter>
    );

    // Switch to security tab
    fireEvent.click(screen.getByText('安全设置'));

    // Wait for form to load
    await waitFor(() => {
      expect(screen.getByLabelText('当前密码')).toBeInTheDocument();
    });

    // Fill password form
    fireEvent.change(screen.getByLabelText('当前密码'), { target: { value: 'current_password' } });
    fireEvent.change(screen.getByLabelText('新密码'), { target: { value: 'new_password123' } });
    fireEvent.change(screen.getByLabelText('确认密码'), { target: { value: 'new_password123' } });

    // Click change password button
    fireEvent.click(screen.getByText('修改密码'));

    // Check if service was called
    await waitFor(() => {
      expect(userSettingsService.changePassword).toHaveBeenCalledWith({
        currentPassword: 'current_password',
        newPassword: 'new_password123',
        confirmPassword: 'new_password123'
      });
    });
  });

  test('handles 2FA enable/disable', async () => {
    render(
      <MemoryRouter>
        <UserSettings />
      </MemoryRouter>
    );

    // Switch to security tab
    fireEvent.click(screen.getByText('安全设置'));

    // Wait for 2FA section to load
    await waitFor(() => {
      expect(screen.getByText('两步验证已启用')).toBeInTheDocument();
    });

    // Click enable 2FA button
    fireEvent.click(screen.getByText('启用两步验证'));

    // Check if service was called
    await waitFor(() => {
      expect(userSettingsService.enable2FA).toHaveBeenCalled();
    });
  });

  test('displays notification settings correctly', async () => {
    render(
      <MemoryRouter>
        <UserSettings />
      </MemoryRouter>
    );

    // Switch to notifications tab
    fireEvent.click(screen.getByText('通知设置'));

    // Check if notification settings are displayed
    await waitFor(() => {
      expect(screen.getByText('邮件通知')).toBeInTheDocument();
      expect(screen.getByText('推送通知')).toBeInTheDocument();
      expect(screen.getByText('短信通知')).toBeInTheDocument();
      expect(screen.getByText('交易提醒')).toBeInTheDocument();
      expect(screen.getByText('风险提醒')).toBeInTheDocument();
      expect(screen.getByText('系统提醒')).toBeInTheDocument();
    });

    // Check if switches are displayed with correct values
    await waitFor(() => {
      expect(screen.getByText('已启用')).toBeInTheDocument();
      expect(screen.getByText('已禁用')).toBeInTheDocument();
    });
  });

  test('handles notification settings changes', async () => {
    render(
      <MemoryRouter>
        <UserSettings />
      </MemoryRouter>
    );

    // Switch to notifications tab
    fireEvent.click(screen.getByText('通知设置'));

    // Wait for switches to load
    await waitFor(() => {
      expect(screen.getByText('邮件通知')).toBeInTheDocument();
    });

    // Toggle email notifications
    const emailSwitch = screen.getAllByRole('switch')[0];
    fireEvent.click(emailSwitch);

    // Check if state is updated
    await waitFor(() => {
      expect(screen.getByText('已禁用')).toBeInTheDocument();
    });
  });

  test('displays trading settings correctly', async () => {
    render(
      <MemoryRouter>
        <UserSettings />
      </MemoryRouter>
    );

    // Switch to trading tab
    fireEvent.click(screen.getByText('交易设置'));

    // Check if trading settings are displayed
    await waitFor(() => {
      expect(screen.getByText('默认交易所')).toBeInTheDocument();
      expect(screen.getByText('默认杠杆')).toBeInTheDocument();
      expect(screen.getByText('每笔交易风险')).toBeInTheDocument();
      expect(screen.getByText('最大每日亏损')).toBeInTheDocument();
      expect(screen.getByText('最大持仓数')).toBeInTheDocument();
      expect(screen.getByText('滑点容忍度')).toBeInTheDocument();
      expect(screen.getByText('自动止损')).toBeInTheDocument();
      expect(screen.getByText('自动止盈')).toBeInTheDocument();
    });
  });

  test('handles trading settings changes', async () => {
    render(
      <MemoryRouter>
        <UserSettings />
      </MemoryRouter>
    );

    // Switch to trading tab
    fireEvent.click(screen.getByText('交易设置'));

    // Wait for settings to load
    await waitFor(() => {
      expect(screen.getByText('默认交易所')).toBeInTheDocument();
    });

    // Change default exchange
    const exchangeSelect = screen.getByDisplayValue('binance');
    fireEvent.change(exchangeSelect, { target: { value: 'gateio' } });

    // Check if value is changed
    expect(screen.getByDisplayValue('gateio')).toBeInTheDocument();
  });

  test('displays exchange configurations correctly', async () => {
    render(
      <MemoryRouter>
        <UserSettings />
      </MemoryRouter>
    );

    // Switch to exchanges tab
    fireEvent.click(screen.getByText('交易所配置'));

    // Check if exchange configurations are displayed
    await waitFor(() => {
      expect(screen.getByText('Binance')).toBeInTheDocument();
      expect(screen.getByText('Gate.io')).toBeInTheDocument();
      expect(screen.getByText('添加交易所')).toBeInTheDocument();
    });

    // Check if exchange details are displayed
    await waitFor(() => {
      expect(screen.getByText('API Key: ********')).toBeInTheDocument();
      expect(screen.getByText('限流: 1200/1m')).toBeInTheDocument();
      expect(screen.getByText('最后同步: 2024-01-15 10:30')).toBeInTheDocument();
    });
  });

  test('handles exchange configuration toggle', async () => {
    render(
      <MemoryRouter>
        <UserSettings />
      </MemoryRouter>
    );

    // Switch to exchanges tab
    fireEvent.click(screen.getByText('交易所配置'));

    // Wait for exchanges to load
    await waitFor(() => {
      expect(screen.getByText('Binance')).toBeInTheDocument();
    });

    // Toggle exchange enable/disable
    const toggleSwitch = screen.getAllByRole('switch')[0];
    fireEvent.click(toggleSwitch);

    // Check if state is updated
    await waitFor(() => {
      expect(screen.getByText('交易所已禁用')).toBeInTheDocument();
    });
  });

  test('handles exchange connection test', async () => {
    render(
      <MemoryRouter>
        <UserSettings />
      </MemoryRouter>
    );

    // Switch to exchanges tab
    fireEvent.click(screen.getByText('交易所配置'));

    // Wait for exchanges to load
    await waitFor(() => {
      expect(screen.getByText('Binance')).toBeInTheDocument();
    });

    // Click test connection button
    const testButton = screen.getAllByText('测试连接')[0];
    fireEvent.click(testButton);

    // Check if service was called
    await waitFor(() => {
      expect(userSettingsService.testExchangeConnection).toHaveBeenCalledWith('1');
    });
  });

  test('displays API settings correctly', async () => {
    render(
      <MemoryRouter>
        <UserSettings />
      </MemoryRouter>
    );

    // Switch to API tab
    fireEvent.click(screen.getByText('API设置'));

    // Check if API settings are displayed
    await waitFor(() => {
      expect(screen.getByText('启用API访问')).toBeInTheDocument();
      expect(screen.getByText('请求限制')).toBeInTheDocument();
      expect(screen.getByText('IP白名单')).toBeInTheDocument();
    });
  });

  test('displays data management settings correctly', async () => {
    render(
      <MemoryRouter>
        <UserSettings />
      </MemoryRouter>
    );

    // Switch to data tab
    fireEvent.click(screen.getByText('数据管理'));

    // Check if data management settings are displayed
    await waitFor(() => {
      expect(screen.getByText('自动备份')).toBeInTheDocument();
      expect(screen.getByText('备份频率')).toBeInTheDocument();
      expect(screen.getByText('保留期限')).toBeInTheDocument();
      expect(screen.getByText('导出格式')).toBeInTheDocument();
      expect(screen.getByText('数据导出')).toBeInTheDocument();
      expect(screen.getByText('数据导入')).toBeInTheDocument();
    });
  });

  test('handles data export', async () => {
    render(
      <MemoryRouter>
        <UserSettings />
      </MemoryRouter>
    );

    // Switch to data tab
    fireEvent.click(screen.getByText('数据管理'));

    // Wait for data management to load
    await waitFor(() => {
      expect(screen.getByText('数据导出')).toBeInTheDocument();
    });

    // Click export CSV button
    fireEvent.click(screen.getByText('导出CSV'));

    // Check if service was called
    await waitFor(() => {
      expect(userSettingsService.exportUserData).toHaveBeenCalledWith({
        format: 'csv',
        includeData: expect.any(Array)
      });
    });
  });

  test('displays system settings correctly', async () => {
    render(
      <MemoryRouter>
        <UserSettings />
      </MemoryRouter>
    );

    // Switch to system tab
    fireEvent.click(screen.getByText('系统设置'));

    // Check if system information is displayed
    await waitFor(() => {
      expect(screen.getByText('系统信息')).toBeInTheDocument();
      expect(screen.getByText('版本')).toBeInTheDocument();
      expect(screen.getByText('构建')).toBeInTheDocument();
      expect(screen.getByText('环境')).toBeInTheDocument();
    });

    // Check if system status is displayed
    await waitFor(() => {
      expect(screen.getByText('数据库状态')).toBeInTheDocument();
      expect(screen.getByText('缓存状态')).toBeInTheDocument();
      expect(screen.getByText('服务状态')).toBeInTheDocument();
    });

    // Check if service status table is displayed
    await waitFor(() => {
      expect(screen.getByText('core-service')).toBeInTheDocument();
      expect(screen.getByText('trading-engine')).toBeInTheDocument();
      expect(screen.getByText('strategy-platform')).toBeInTheDocument();
      expect(screen.getByText('notification-service')).toBeInTheDocument();
    });
  });

  test('handles loading state', () => {
    // Mock services to return promises that don't resolve immediately
    (userSettingsService.getUserConfig as jest.Mock).mockReturnValue(new Promise(() => {}));
    (userSettingsService.getExchangeConfigs as jest.Mock).mockReturnValue(new Promise(() => {}));
    (userSettingsService.getSystemConfig as jest.Mock).mockReturnValue(new Promise(() => {}));

    render(
      <MemoryRouter>
        <UserSettings />
      </MemoryRouter>
    );

    // Check if loading state is handled
    expect(screen.getByText('用户设置和配置')).toBeInTheDocument();
  });

  test('handles error state', async () => {
    (userSettingsService.getUserConfig as jest.Mock).mockRejectedValue(new Error('API Error'));
    (userSettingsService.getExchangeConfigs as jest.Mock).mockRejectedValue(new Error('API Error'));
    (userSettingsService.getSystemConfig as jest.Mock).mockRejectedValue(new Error('API Error'));

    render(
      <MemoryRouter>
        <UserSettings />
      </MemoryRouter>
    );

    // Check if error is handled gracefully
    await waitFor(() => {
      expect(screen.getByText('用户设置和配置')).toBeInTheDocument();
    });
  });

  test('handles tab navigation correctly', async () => {
    render(
      <MemoryRouter>
        <UserSettings />
      </MemoryRouter>
    );

    // Test navigating through all tabs
    const tabs = [
      '个人资料',
      '安全设置',
      '通知设置',
      '交易设置',
      '交易所配置',
      'API设置',
      '数据管理',
      '系统设置'
    ];

    for (const tab of tabs) {
      fireEvent.click(screen.getByText(tab));
      await waitFor(() => {
        expect(screen.getByText(tab)).toBeInTheDocument();
      });
    }
  });

  test('handles form validation errors', async () => {
    render(
      <MemoryRouter>
        <UserSettings />
      </MemoryRouter>
    );

    // Switch to profile tab
    fireEvent.click(screen.getByText('个人资料'));

    // Wait for form to load
    await waitFor(() => {
      expect(screen.getByLabelText('用户名')).toBeInTheDocument();
    });

    // Clear required fields
    fireEvent.change(screen.getByLabelText('用户名'), { target: { value: '' } });
    fireEvent.change(screen.getByLabelText('邮箱'), { target: { value: '' } });

    // Click save button
    fireEvent.click(screen.getByText('保存设置'));

    // Check if validation errors are displayed
    await waitFor(() => {
      expect(screen.getByText('请输入用户名')).toBeInTheDocument();
      expect(screen.getByText('请输入有效邮箱')).toBeInTheDocument();
    });
  });

  test('handles password confirmation validation', async () => {
    render(
      <MemoryRouter>
        <UserSettings />
      </MemoryRouter>
    );

    // Switch to security tab
    fireEvent.click(screen.getByText('安全设置'));

    // Wait for form to load
    await waitFor(() => {
      expect(screen.getByLabelText('当前密码')).toBeInTheDocument();
    });

    // Fill password form with mismatched passwords
    fireEvent.change(screen.getByLabelText('当前密码'), { target: { value: 'current_password' } });
    fireEvent.change(screen.getByLabelText('新密码'), { target: { value: 'new_password123' } });
    fireEvent.change(screen.getByLabelText('确认密码'), { target: { value: 'different_password' } });

    // Click change password button
    fireEvent.click(screen.getByText('修改密码'));

    // Check if validation error is displayed
    await waitFor(() => {
      expect(screen.getByText('两次输入的密码不一致')).toBeInTheDocument();
    });
  });
});

export default UserSettings;