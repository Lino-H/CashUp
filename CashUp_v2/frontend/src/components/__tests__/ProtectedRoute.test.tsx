import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Navigate } from 'react-router-dom';
import { ProtectedRoute } from '../ProtectedRoute';
import { AuthProvider, useAuth } from '../../contexts/AuthContext';

// Mock the AuthContext
const MockAuthProvider: React.FC<{ children: React.ReactNode; isAuthenticated?: boolean; loading?: boolean }> = ({ 
  children, 
  isAuthenticated = false, 
  loading = false 
}) => {
  const mockUseAuth = jest.fn(() => ({
    isAuthenticated,
    loading,
    login: jest.fn(),
    logout: jest.fn(),
    user: null,
  }));

  jest.mock('../../contexts/AuthContext', () => ({
    ...jest.requireActual('../../contexts/AuthContext'),
    useAuth: mockUseAuth,
  }));

  return <>{children}</>;
};

const TestChild: React.FC = () => <div>Test Content</div>;

describe('ProtectedRoute', () => {
  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();
  });

  test('should render loading state when authentication is loading', () => {
    render(
      <MemoryRouter>
        <MockAuthProvider loading={true}>
          <ProtectedRoute>
            <TestChild />
          </ProtectedRoute>
        </MockAuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  test('should redirect to login when not authenticated', () => {
    render(
      <MemoryRouter initialEntries={['/protected']}>
        <MockAuthProvider isAuthenticated={false}>
          <ProtectedRoute>
            <TestChild />
          </ProtectedRoute>
        </MockAuthProvider>
      </MemoryRouter>
    );

    // Should not render the child content
    expect(screen.queryByText('Test Content')).not.toBeInTheDocument();
    
    // Should have navigated to login
    expect(window.location.pathname).toBe('/login');
  });

  test('should render children when authenticated', () => {
    render(
      <MemoryRouter initialEntries={['/protected']}>
        <MockAuthProvider isAuthenticated={true}>
          <ProtectedRoute>
            <TestChild />
          </ProtectedRoute>
        </MockAuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  test('should preserve route state when redirecting', () => {
    render(
      <MemoryRouter initialEntries={['/protected?param=value']}>
        <MockAuthProvider isAuthenticated={false}>
          <ProtectedRoute>
            <TestChild />
          </ProtectedRoute>
        </MockAuthProvider>
      </MemoryRouter>
    );

    // Check that the redirect happened and state was preserved
    expect(window.location.pathname).toBe('/login');
    expect(window.location.search).toBe('?redirect=/protected%3Fparam%3Dvalue');
  });

  test('should handle authentication state changes', () => {
    const { rerender } = render(
      <MemoryRouter initialEntries={['/protected']}>
        <MockAuthProvider isAuthenticated={false}>
          <ProtectedRoute>
            <TestChild />
          </ProtectedRoute>
        </MockAuthProvider>
      </MemoryRouter>
    );

    // Initially should redirect
    expect(screen.queryByText('Test Content')).not.toBeInTheDocument();

    // Rerender with authenticated state
    rerender(
      <MemoryRouter initialEntries={['/protected']}>
        <MockAuthProvider isAuthenticated={true}>
          <ProtectedRoute>
            <TestChild />
          </ProtectedRoute>
        </MockAuthProvider>
      </MemoryRouter>
    );

    // Now should render children
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  test('should handle different child components', () => {
    const DifferentChild: React.FC = () => <div>Different Content</div>;
    
    render(
      <MemoryRouter initialEntries={['/protected']}>
        <MockAuthProvider isAuthenticated={true}>
          <ProtectedRoute>
            <DifferentChild />
          </ProtectedRoute>
        </MockAuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText('Different Content')).toBeInTheDocument();
  });
});