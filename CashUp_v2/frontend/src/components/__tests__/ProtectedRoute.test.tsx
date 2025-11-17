import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route, useLocation } from 'react-router-dom';
import { ProtectedRoute } from '../ProtectedRoute';
/**
 * 函数集注释：
 * - 使用顶层 jest.mock 伪造 useAuth，按场景返回不同认证状态
 * - 使用 MemoryRouter + Routes 正确验证导航与重定向查询参数
 */
import { useAuth } from '../../contexts/AuthContext';

jest.mock('../../contexts/AuthContext', () => {
  const actual = jest.requireActual('../../contexts/AuthContext');
  return {
    ...actual,
    useAuth: jest.fn(),
  };
});

const TestChild: React.FC = () => <div>Test Content</div>;

const LoginProbe: React.FC = () => {
  const location = useLocation();
  return (
    <div>
      <div>Login Page</div>
      <div data-testid="search">{location.search}</div>
    </div>
  );
};

describe('ProtectedRoute', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('显示加载态：loading=true', () => {
    (useAuth as jest.Mock).mockReturnValue({ isAuthenticated: false, loading: true });
    render(
      <MemoryRouter initialEntries={['/protected']}>
        <Routes>
          <Route path="/protected" element={<ProtectedRoute><TestChild /></ProtectedRoute>} />
          <Route path="/login" element={<LoginProbe />} />
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  test('未登录重定向到 /login', () => {
    (useAuth as jest.Mock).mockReturnValue({ isAuthenticated: false, loading: false });
    render(
      <MemoryRouter initialEntries={['/protected']}>
        <Routes>
          <Route path="/protected" element={<ProtectedRoute><TestChild /></ProtectedRoute>} />
          <Route path="/login" element={<LoginProbe />} />
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByText('Login Page')).toBeInTheDocument();
    expect(screen.queryByText('Test Content')).not.toBeInTheDocument();
  });

  test('登录后可访问受保护内容', () => {
    (useAuth as jest.Mock).mockReturnValue({ isAuthenticated: true, loading: false });
    render(
      <MemoryRouter initialEntries={['/protected']}>
        <Routes>
          <Route path="/protected" element={<ProtectedRoute><TestChild /></ProtectedRoute>} />
          <Route path="/login" element={<LoginProbe />} />
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  test('重定向携带来源路由查询参数', () => {
    (useAuth as jest.Mock).mockReturnValue({ isAuthenticated: false, loading: false });
    render(
      <MemoryRouter initialEntries={['/protected?param=value']}>
        <Routes>
          <Route path="/protected" element={<ProtectedRoute><TestChild /></ProtectedRoute>} />
          <Route path="/login" element={<LoginProbe />} />
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByTestId('search').textContent).toBe('?redirect=%2Fprotected%3Fparam%3Dvalue');
  });

  test('认证状态变化后渲染受保护内容', () => {
    const mock = useAuth as jest.Mock;
    mock.mockReturnValue({ isAuthenticated: false, loading: false });
    render(
      <MemoryRouter initialEntries={['/protected']}>
        <Routes>
          <Route path="/protected" element={<ProtectedRoute><TestChild /></ProtectedRoute>} />
          <Route path="/login" element={<LoginProbe />} />
        </Routes>
      </MemoryRouter>
    );
    expect(screen.queryByText('Test Content')).not.toBeInTheDocument();
    mock.mockReturnValue({ isAuthenticated: true, loading: false });
    render(
      <MemoryRouter initialEntries={['/protected']}>
        <Routes>
          <Route path="/protected" element={<ProtectedRoute><TestChild /></ProtectedRoute>} />
          <Route path="/login" element={<LoginProbe />} />
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  test('不同子组件正常渲染', () => {
    (useAuth as jest.Mock).mockReturnValue({ isAuthenticated: true, loading: false });
    const DifferentChild: React.FC = () => <div>Different Content</div>;
    render(
      <MemoryRouter initialEntries={['/protected']}>
        <Routes>
          <Route path="/protected" element={<ProtectedRoute><DifferentChild /></ProtectedRoute>} />
          <Route path="/login" element={<LoginProbe />} />
        </Routes>
      </MemoryRouter>
    );
    expect(screen.getByText('Different Content')).toBeInTheDocument();
  });
});