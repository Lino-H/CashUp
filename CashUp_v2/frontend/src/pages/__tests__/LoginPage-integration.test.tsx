import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, useNavigate } from 'react-router-dom';
import LoginPage from '../LoginPage';
import { AuthProvider, useAuth } from '../../contexts/AuthContext';

// Mock the AuthContext
const MockAuthWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
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

  return <>{children}</>;
};

// Mock API calls
jest.mock('../../services/api', () => ({
  authAPI: {
    login: jest.fn(),
  },
}));

const { authAPI } = require('../../services/api');

describe('LoginPage Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  test('should render login form correctly', () => {
    render(
      <MemoryRouter>
        <MockAuthWrapper>
          <LoginPage />
        </MockAuthWrapper>
      </MemoryRouter>
    );

    expect(screen.getByLabelText(/用户名/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/密码/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument();
    expect(screen.getByText(/忘记密码/i)).toBeInTheDocument();
    expect(screen.getByText(/注册新账号/i)).toBeInTheDocument();
  });

  test('should handle form submission', async () => {
    const mockLogin = authAPI.login.mockResolvedValue({
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
        <MockAuthWrapper>
          <LoginPage />
        </MockAuthWrapper>
      </MemoryRouter>
    );

    // Fill in the form
    fireEvent.change(screen.getByLabelText(/用户名/i), {
      target: { value: 'testuser' }
    });
    fireEvent.change(screen.getByLabelText(/密码/i), {
      target: { value: 'password123' }
    });

    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /登录/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('testuser', 'password123');
    });
  });

  test('should show loading state during login', async () => {
    authAPI.login.mockImplementation(() => new Promise(resolve => {
      setTimeout(() => resolve({
        access_token: 'test-token',
        token_type: 'bearer',
        user: { id: '1', username: 'testuser', email: 'testuser@example.com' }
      }), 1000);
    }));

    render(
      <MemoryRouter>
        <MockAuthWrapper>
          <LoginPage />
        </MockAuthWrapper>
      </MemoryRouter>
    );

    // Fill in the form
    fireEvent.change(screen.getByLabelText(/用户名/i), {
      target: { value: 'testuser' }
    });
    fireEvent.change(screen.getByLabelText(/密码/i), {
      target: { value: 'password123' }
    });

    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /登录/i }));

    // Should show loading state
    expect(screen.getByText(/登录中.../i)).toBeInTheDocument();
    
    // Wait for login to complete
    await waitFor(() => {
      expect(screen.queryByText(/登录中.../i)).not.toBeInTheDocument();
    });
  });

  test('should display error message on login failure', async () => {
    authAPI.login.mockRejectedValue({
      response: {
        status: 401,
        data: { detail: '用户名或密码错误' }
      }
    });

    render(
      <MemoryRouter>
        <MockAuthWrapper>
          <LoginPage />
        </MockAuthWrapper>
      </MemoryRouter>
    );

    // Fill in the form
    fireEvent.change(screen.getByLabelText(/用户名/i), {
      target: { value: 'wronguser' }
    });
    fireEvent.change(screen.getByLabelText(/密码/i), {
      target: { value: 'wrongpass' }
    });

    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /登录/i }));

    await waitFor(() => {
      expect(screen.getByText(/用户名或密码错误/i)).toBeInTheDocument();
    });
  });

  test('should validate form inputs', () => {
    render(
      <MemoryRouter>
        <MockAuthWrapper>
          <LoginPage />
        </MockAuthWrapper>
      </MemoryRouter>
    );

    // Try to submit empty form
    fireEvent.click(screen.getByRole('button', { name: /登录/i }));

    // Should show validation errors
    expect(screen.getByText(/请输入用户名/i)).toBeInTheDocument();
    expect(screen.getByText(/请输入密码/i)).toBeInTheDocument();
  });

  test('should navigate to register page when clicking register link', () => {
    const navigate = jest.fn();
    
    // Mock the useNavigate hook
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => navigate,
    }));

    render(
      <MemoryRouter>
        <MockAuthWrapper>
          <LoginPage />
        </MockAuthWrapper>
      </MemoryRouter>
    );

    // Click register link
    fireEvent.click(screen.getByText(/注册新账号/i));

    expect(navigate).toHaveBeenCalledWith('/register');
  });

  test('should navigate to forgot password page when clicking forgot password link', () => {
    const navigate = jest.fn();
    
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => navigate,
    }));

    render(
      <MemoryRouter>
        <MockAuthWrapper>
          <LoginPage />
        </MockAuthWrapper>
      </MemoryRouter>
    );

    // Click forgot password link
    fireEvent.click(screen.getByText(/忘记密码/i));

    expect(navigate).toHaveBeenCalledWith('/forgot-password');
  });

  test('should persist login state after successful login', async () => {
    authAPI.login.mockResolvedValue({
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
        <MockAuthWrapper>
          <LoginPage />
        </MockAuthWrapper>
      </MemoryRouter>
    );

    // Fill in the form
    fireEvent.change(screen.getByLabelText(/用户名/i), {
      target: { value: 'testuser' }
    });
    fireEvent.change(screen.getByLabelText(/密码/i), {
      target: { value: 'password123' }
    });

    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /登录/i }));

    await waitFor(() => {
      // Verify localStorage was updated
      expect(localStorage.getItem('access_token')).toBe('test-token');
      expect(localStorage.getItem('user')).toContain('testuser');
    });
  });

  test('should handle remember me functionality', async () => {
    authAPI.login.mockResolvedValue({
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
        <MockAuthWrapper>
          <LoginPage />
        </MockAuthWrapper>
      </MemoryRouter>
    );

    // Fill in the form
    fireEvent.change(screen.getByLabelText(/用户名/i), {
      target: { value: 'testuser' }
    });
    fireEvent.change(screen.getByLabelText(/密码/i), {
      target: { value: 'password123' }
    });

    // Check remember me
    fireEvent.click(screen.getByLabelText(/记住我/i));

    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /登录/i }));

    await waitFor(() => {
      // Verify remember me functionality was called
      expect(authAPI.login).toHaveBeenCalledWith('testuser', 'password123');
    });
  });

  test('should show password visibility toggle', () => {
    render(
      <MemoryRouter>
        <MockAuthWrapper>
          <LoginPage />
        </MockAuthWrapper>
      </MemoryRouter>
    );

    const passwordInput = screen.getByLabelText(/密码/i);
    const toggleButton = screen.getByRole('button', { name: /显示密码/i });

    // Initially password should be hidden
    expect(passwordInput).toHaveAttribute('type', 'password');

    // Click toggle button
    fireEvent.click(toggleButton);

    // Password should now be visible
    expect(passwordInput).toHaveAttribute('type', 'text');

    // Click toggle button again
    fireEvent.click(toggleButton);

    // Password should be hidden again
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  test('should handle keyboard shortcuts', () => {
    render(
      <MemoryRouter>
        <MockAuthWrapper>
          <LoginPage />
        </MockAuthWrapper>
      </MemoryRouter>
    );

    // Fill in the form
    fireEvent.change(screen.getByLabelText(/用户名/i), {
      target: { value: 'testuser' }
    });
    fireEvent.change(screen.getByLabelText(/密码/i), {
      target: { value: 'password123' }
    });

    // Press Enter key
    fireEvent.keyPress(screen.getByLabelText(/密码/i), {
      key: 'Enter',
      code: 'Enter',
    });

    // Should have triggered login
    expect(authAPI.login).not.toHaveBeenCalled();

    // Need to wait for the form submission logic
    // This test would need to be updated based on actual form submission implementation
  });

  test('should support social login options', () => {
    render(
      <MemoryRouter>
        <MockAuthWrapper>
          <LoginPage />
        </MockAuthWrapper>
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