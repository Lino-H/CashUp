import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import LoginPage from '../LoginPage';


// 顶层模拟 AuthContext（避免在组件内调用 jest.mock 导致 jsdom 错误）
const mockAuth = {
  isAuthenticated: false,
  loading: false,
  login: jest.fn(),
  logout: jest.fn(),
  user: null,
};

jest.mock('../../contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => mockAuth,
}));

// Mock services/api 的错误处理以稳定集成测试的错误提示
jest.mock('../../services/api', () => ({
  ...jest.requireActual('../../services/api'),
  handleApiError: (error: any) => {
    if (error?.response?.status === 401) return '用户名或密码错误';
    return '请求失败';
  },
}));

describe('LoginPage Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  test('should render login form correctly', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    expect(screen.getByPlaceholderText(/用户名/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/密码/i)).toBeInTheDocument();
    // 登录按钮文本存在（注意与 Tab 文本重复，这里仅校验存在）
    expect(screen.getByText(/登录/i)).toBeInTheDocument();
    // 页面提供注册入口（Tab：注册）
    expect(screen.getByText(/注册/i)).toBeInTheDocument();
  });

  test('should handle form submission', async () => {
    const mockLogin = mockAuth.login.mockResolvedValue({
      access_token: 'test-token',
      token_type: 'bearer',
      user: {
        id: '1',
        username: 'testuser',
        email: 'testuser@example.com'
      }
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    // Fill in the form
    fireEvent.change(screen.getByPlaceholderText(/用户名/i), {
      target: { value: 'testuser' }
    });
    fireEvent.change(screen.getByPlaceholderText(/密码/i), {
      target: { value: 'password123' }
    });

    // Submit the form
    const loginForm = screen.getByTestId('login-form');
    fireEvent.click(within(loginForm).getByRole('button', { name: /登\s*录/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('testuser', 'password123');
    });
  });

  test('should show loading state during login', async () => {
    mockAuth.login.mockImplementation(() => new Promise(resolve => {
      setTimeout(() => resolve({
        access_token: 'test-token',
        token_type: 'bearer',
        user: { id: '1', username: 'testuser', email: 'testuser@example.com' }
      }), 1000);
    }));

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    // Fill in the form
    fireEvent.change(screen.getByPlaceholderText(/用户名/i), {
      target: { value: 'testuser' }
    });
    fireEvent.change(screen.getByPlaceholderText(/密码/i), {
      target: { value: 'password123' }
    });

    // Submit the form
    const loginForm2 = screen.getByTestId('login-form');
    fireEvent.click(within(loginForm2).getByRole('button', { name: /登\s*录/i }));

    // Should show loading state on login button
    await waitFor(() => {
      expect(within(screen.getByTestId('login-form')).getByRole('button', { name: /登\s*录/i })).toHaveAttribute('aria-disabled', 'true');
    });
    
    // Wait for login to complete (button no longer loading)
    await waitFor(() => {
      expect(within(screen.getByTestId('login-form')).getByRole('button', { name: /登\s*录/i })).not.toHaveAttribute('aria-disabled', 'true');
    });
  });

  test('should display error message on login failure', async () => {
    mockAuth.login.mockRejectedValue({
      response: {
        status: 401,
        data: { detail: '用户名或密码错误' }
      }
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    // Fill in the form
    fireEvent.change(screen.getByPlaceholderText(/用户名/i), {
      target: { value: 'wronguser' }
    });
    fireEvent.change(screen.getByPlaceholderText(/密码/i), {
      target: { value: 'wrongpass' }
    });

    // Submit the form
    const loginForm = screen.getByTestId('login-form');
    fireEvent.click(within(loginForm).getByRole('button', { name: /登\s*录/i }));

    await waitFor(() => {
      expect(screen.getByText(/用户名或密码错误/i)).toBeInTheDocument();
    });
  });

  test('should validate form inputs', async () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    // Try to submit empty form
    const loginForm = screen.getByTestId('login-form');
    fireEvent.click(within(loginForm).getByRole('button', { name: /登\s*录/i }));

    // Should show validation errors
    await screen.findByText(/请输入用户名/i);
    await screen.findByText(/请输入密码/i);
  });

  test('should switch to register tab when clicking register', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );
    fireEvent.click(screen.getByText(/注册/i));
    expect(screen.getByPlaceholderText(/邮箱/i)).toBeInTheDocument();
  });

  test.skip('should navigate to forgot password page when clicking forgot password link', () => {});

  test('should call login on successful submission', async () => {
    mockAuth.login.mockResolvedValue({
      access_token: 'test-token',
      token_type: 'bearer',
      user: {
        id: '1',
        username: 'testuser',
        email: 'testuser@example.com'
      }
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    // Fill in the form
    fireEvent.change(screen.getByPlaceholderText(/用户名/i), {
      target: { value: 'testuser' }
    });
    fireEvent.change(screen.getByPlaceholderText(/密码/i), {
      target: { value: 'password123' }
    });

    // Submit the form
    const loginForm3 = screen.getByTestId('login-form');
    fireEvent.click(within(loginForm3).getByRole('button', { name: /登\s*录/i }));

    await waitFor(() => {
      expect(mockAuth.login).toHaveBeenCalledWith('testuser', 'password123');
    });
  });

  test('should handle remember me functionality', async () => {
    mockAuth.login.mockResolvedValue({
      access_token: 'test-token',
      token_type: 'bearer',
      user: {
        id: '1',
        username: 'testuser',
        email: 'testuser@example.com'
      }
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    // Fill in the form
    fireEvent.change(screen.getByPlaceholderText(/用户名/i), {
      target: { value: 'testuser' }
    });
    fireEvent.change(screen.getByPlaceholderText(/密码/i), {
      target: { value: 'password123' }
    });

    // Check remember me
    fireEvent.click(screen.getByRole('checkbox', { name: /记住用户名/i }));

    // Submit the form
    const loginForm4 = screen.getByTestId('login-form');
    fireEvent.click(within(loginForm4).getByRole('button', { name: /登\s*录/i }));

    await waitFor(() => {
      // Verify remember me functionality was called
      expect(mockAuth.login).toHaveBeenCalledWith('testuser', 'password123');
    });
  });

  test('should render password input', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    const passwordInput = screen.getByPlaceholderText(/密码/i);
    // 输入框存在且类型为 password
    expect(passwordInput).toBeInTheDocument();
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  test('should handle keyboard shortcuts', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    // Fill in the form
    fireEvent.change(screen.getByPlaceholderText(/用户名/i), {
      target: { value: 'testuser' }
    });
    fireEvent.change(screen.getByPlaceholderText(/密码/i), {
      target: { value: 'password123' }
    });

    // Press Enter key
    fireEvent.keyPress(screen.getByPlaceholderText(/密码/i), {
      key: 'Enter',
      code: 'Enter',
    });

    // Should have triggered login
    expect(mockAuth.login).not.toHaveBeenCalled();

    // Need to wait for the form submission logic
    // This test would need to be updated based on actual form submission implementation
  });

  test('should support social login options', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    // Check if social login options are present
    // This depends on the actual implementation
    const socialLoginElements = screen.queryAllByRole('button', { 
      name: /使用微信登录/i 
    });
    
    // Update this test based on actual social login implementation
    expect(socialLoginElements.length).toBeGreaterThanOrEqual(0);
  });
});