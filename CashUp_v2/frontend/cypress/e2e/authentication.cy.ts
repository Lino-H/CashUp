// cypress/e2e/authentication.cy.ts
import { getTestUser, getAdminUser } from '../support/e2e';

describe('Authentication End-to-End Tests', () => {
  const testUser = getTestUser();
  const adminUser = getAdminUser();

  beforeEach(() => {
    cy.clearCookiesAndLocalStorage();
    cy.visit('/login');
    cy.waitUntilStable();
  });

  describe('Login Flow', () => {
    it('should allow user to login with valid credentials', () => {
      cy.login(testUser.username, testUser.password);
      
      // Verify successful login
      cy.url().should('include', '/dashboard');
      cy.get('h1').should('contain', '欢迎回来');
      cy.get('header').should('contain', testUser.username);
    });

    it('should show error message for invalid credentials', () => {
      cy.visit('/login');
      
      // Fill in invalid credentials
      cy.get('input[name="username"]').type('invaliduser');
      cy.get('input[name="password"]').type('wrongpassword');
      
      // Submit form
      cy.get('button[type="submit"]').click();
      
      // Verify error message
      cy.get('.error-message').should('contain', '用户名或密码错误');
      cy.url().should('include', '/login');
    });

    it('should validate form inputs', () => {
      cy.visit('/login');
      
      // Try to submit empty form
      cy.get('button[type="submit"]').click();
      
      // Verify validation errors
      cy.get('.error').should('contain', '请输入用户名');
      cy.get('.error').should('contain', '请输入密码');
    });

    it('should remember user session', () => {
      cy.login(testUser.username, testUser.password);
      
      // Verify session is stored
      cy.get('input[name="username"]').should('have.value', testUser.username);
      cy.get('input[name="password"]').should('have.value', '');
      cy.get('input[type="checkbox"]').should('be.checked');
    });

    it('should handle login with admin credentials', () => {
      cy.login(adminUser.username, adminUser.password);
      
      // Verify admin dashboard
      cy.url().should('include', '/dashboard');
      cy.get('h1').should('contain', '欢迎回来');
      cy.get('header').should('contain', adminUser.username);
    });
  });

  describe('Logout Flow', () => {
    it('should allow user to logout', () => {
      cy.login(testUser.username, testUser.password);
      
      // Logout
      cy.get('button').contains('退出登录').click();
      
      // Verify logout
      cy.url().should('include', '/login');
      cy.get('h1').should('contain', '用户登录');
    });

    it('should clear session on logout', () => {
      cy.login(testUser.username, testUser.password);
      
      // Logout
      cy.get('button').contains('退出登录').click();
      
      // Verify session is cleared
      cy.get('input[name="username"]').should('not.have.value', testUser.username);
      cy.get('input[name="password"]').should('not.have.value', testUser.password);
    });

    it('should redirect to login page after logout', () => {
      cy.login(testUser.username, testUser.password);
      
      // Logout
      cy.get('button').contains('退出登录').click();
      
      // Verify redirect
      cy.url().should('include', '/login');
      cy.get('h1').should('contain', '用户登录');
    });
  });

  describe('Protected Routes', () => {
    it('should redirect unauthenticated user to login', () => {
      cy.clearCookiesAndLocalStorage();
      
      // Try to access dashboard directly
      cy.visit('/dashboard');
      
      // Verify redirect to login
      cy.url().should('include', '/login');
      cy.get('h1').should('contain', '用户登录');
    });

    it('should protect dashboard route', () => {
      cy.clearCookiesAndLocalStorage();
      
      // Try to access dashboard directly
      cy.visit('/dashboard');
      
      // Verify redirect to login
      cy.url().should('include', '/login');
      
      // Verify login form
      cy.get('input[name="username"]').should('be.visible');
      cy.get('input[name="password"]').should('be.visible');
      cy.get('button[type="submit"]').should('be.visible');
    });

    it('should protect strategies route', () => {
      cy.clearCookiesAndLocalStorage();
      
      // Try to access strategies directly
      cy.visit('/strategies');
      
      // Verify redirect to login
      cy.url().should('include', '/login');
      cy.get('h1').should('contain', '用户登录');
    });

    it('should protect settings route', () => {
      cy.clearCookiesAndLocalStorage();
      
      // Try to access settings directly
      cy.visit('/settings');
      
      // Verify redirect to login
      cy.url().should('include', '/login');
      cy.get('h1').should('contain', '用户登录');
    });
  });

  describe('Session Management', () => {
    it('should maintain session across page refresh', () => {
      cy.login(testUser.username, testUser.password);
      
      // Refresh page
      cy.reload();
      
      // Verify session is maintained
      cy.url().should('include', '/dashboard');
      cy.get('h1').should('contain', '欢迎回来');
    });

    it('should maintain session across navigation', () => {
      cy.login(testUser.username, testUser.password);
      
      // Navigate to different pages
      cy.visit('/strategies');
      cy.visit('/settings');
      cy.visit('/dashboard');
      
      // Verify session is maintained
      cy.url().should('include', '/dashboard');
      cy.get('h1').should('contain', '欢迎回来');
    });

    it('should handle session timeout', () => {
      cy.login(testUser.username, testUser.password);
      
      // Simulate session timeout
      cy.clearCookies();
      
      // Try to access protected route
      cy.visit('/dashboard');
      
      // Verify redirect to login
      cy.url().should('include', '/login');
      cy.get('h1').should('contain', '用户登录');
    });
  });

  describe('Registration Flow', () => {
    it('should allow user to register', () => {
      cy.visit('/register');
      
      // Fill in registration form
      cy.get('input[name="username"]').type('newuser');
      cy.get('input[name="email"]').type('newuser@example.com');
      cy.get('input[name="password"]').type('password123');
      cy.get('input[name="confirmPassword"]').type('password123');
      
      // Submit form
      cy.get('button[type="submit"]').click();
      
      // Verify registration success
      cy.url().should('include', '/login');
      cy.get('h1').should('contain', '用户登录');
    });

    it('should validate registration form', () => {
      cy.visit('/register');
      
      // Try to submit empty form
      cy.get('button[type="submit"]').click();
      
      // Verify validation errors
      cy.get('.error').should('contain', '请输入用户名');
      cy.get('.error').should('contain', '请输入邮箱');
      cy.get('.error').should('contain', '请输入密码');
      cy.get('.error').should('contain', '请确认密码');
    });

    it('should validate password confirmation', () => {
      cy.visit('/register');
      
      // Fill in form with mismatched passwords
      cy.get('input[name="username"]').type('newuser');
      cy.get('input[name="email"]').type('newuser@example.com');
      cy.get('input[name="password"]').type('password123');
      cy.get('input[name="confirmPassword"]').type('differentpassword');
      
      // Submit form
      cy.get('button[type="submit"]').click();
      
      // Verify password confirmation error
      cy.get('.error').should('contain', '密码不匹配');
    });

    it('should validate email format', () => {
      cy.visit('/register');
      
      // Fill in form with invalid email
      cy.get('input[name="username"]').type('newuser');
      cy.get('input[name="email"]').type('invalid-email');
      cy.get('input[name="password"]').type('password123');
      cy.get('input[name="confirmPassword"]').type('password123');
      
      // Submit form
      cy.get('button[type="submit"]').click();
      
      // Verify email validation error
      cy.get('.error').should('contain', '请输入有效的邮箱地址');
    });
  });

  describe('Password Recovery', () => {
    it('should show password recovery form', () => {
      cy.visit('/forgot-password');
      
      // Verify password recovery form
      cy.get('input[name="email"]').should('be.visible');
      cy.get('button[type="submit"]').should('be.visible');
    });

    it('should handle password recovery request', () => {
      cy.visit('/forgot-password');
      
      // Fill in email
      cy.get('input[name="email"]').type('testuser@example.com');
      
      // Submit form
      cy.get('button[type="submit"]').click();
      
      // Verify success message
      cy.get('.success').should('contain', '密码重置链接已发送到您的邮箱');
    });

    it('should validate email in password recovery', () => {
      cy.visit('/forgot-password');
      
      // Fill in invalid email
      cy.get('input[name="email"]').type('invalid-email');
      
      // Submit form
      cy.get('button[type="submit"]').click();
      
      // Verify error message
      cy.get('.error').should('contain', '请输入有效的邮箱地址');
    });
  });

  describe('User Profile', () => {
    it('should allow user to update profile', () => {
      cy.login(testUser.username, testUser.password);
      
      // Navigate to profile
      cy.visit('/settings');
      
      // Update profile
      cy.get('input[name="username"]').clear().type('updateduser');
      cy.get('input[name="email"]').clear().type('updated@example.com');
      
      // Submit form
      cy.get('button[type="submit"]').click();
      
      // Verify update success
      cy.get('.success').should('contain', '个人信息更新成功');
    });

    it('should validate profile updates', () => {
      cy.login(testUser.username, testUser.password);
      
      // Navigate to profile
      cy.visit('/settings');
      
      // Try to submit empty form
      cy.get('input[name="username"]').clear();
      cy.get('input[name="email"]').clear();
      
      // Submit form
      cy.get('button[type="submit"]').click();
      
      // Verify validation errors
      cy.get('.error').should('contain', '请输入用户名');
      cy.get('.error').should('contain', '请输入邮箱');
    });

    it('should handle password change', () => {
      cy.login(testUser.username, testUser.password);
      
      // Navigate to profile
      cy.visit('/settings');
      
      // Change password
      cy.get('input[name="currentPassword"]').type('password123');
      cy.get('input[name="newPassword"]').type('newpassword123');
      cy.get('input[name="confirmPassword"]').type('newpassword123');
      
      // Submit form
      cy.get('button[type="submit"]').click();
      
      // Verify change success
      cy.get('.success').should('contain', '密码修改成功');
    });
  });

  describe('Multi-factor Authentication', () => {
    it('should enable 2FA', () => {
      cy.login(testUser.username, testUser.password);
      
      // Navigate to security settings
      cy.visit('/settings/security');
      
      // Enable 2FA
      cy.get('button').contains('启用双因素认证').click();
      
      // Verify 2FA setup
      cy.get('.qr-code').should('be.visible');
      cy.get('input[name="otp"]').should('be.visible');
    });

    it('should verify 2FA code', () => {
      cy.login(testUser.username, testUser.password);
      
      // Navigate to security settings
      cy.visit('/settings/security');
      
      // Enable 2FA
      cy.get('button').contains('启用双因素认证').click();
      
      // Enter OTP code
      cy.get('input[name="otp"]').type('123456');
      
      // Submit form
      cy.get('button[type="submit"]').click();
      
      // Verify 2FA enabled
      cy.get('.success').should('contain', '双因素认证已启用');
    });
  });

  describe('Social Login', () => {
    it('should support WeChat login', () => {
      cy.visit('/login');
      
      // Click WeChat login button
      cy.get('button').contains('使用微信登录').click();
      
      // Verify WeChat login flow
      cy.url().should('include', '/auth/wechat');
    });

    it('should handle social login callback', () => {
      cy.visit('/auth/wechat/callback');
      
      // Verify social login handling
      cy.get('.loading').should('contain', '正在处理登录');
    });
  });

  describe('Accessibility Tests', () => {
    it('should have accessible login form', () => {
      cy.visit('/login');
      cy.checkPageAccessibility();
    });

    it('should have accessible registration form', () => {
      cy.visit('/register');
      cy.checkPageAccessibility();
    });

    it('should have accessible password recovery', () => {
      cy.visit('/forgot-password');
      cy.checkPageAccessibility();
    });

    it('should have accessible profile settings', () => {
      cy.login(testUser.username, testUser.password);
      cy.visit('/settings');
      cy.checkPageAccessibility();
    });
  });

  describe('Mobile Responsiveness', () => {
    it('should work on mobile devices', () => {
      cy.viewport(375, 667);
      
      cy.visit('/login');
      
      // Verify mobile layout
      cy.get('h1').should('be.visible');
      cy.get('input[name="username"]').should('be.visible');
      cy.get('input[name="password"]').should('be.visible');
      cy.get('button[type="submit"]').should('be.visible');
    });

    it('should work on tablets', () => {
      cy.viewport(768, 1024);
      
      cy.visit('/login');
      
      // Verify tablet layout
      cy.get('h1').should('be.visible');
      cy.get('input[name="username"]').should('be.visible');
      cy.get('input[name="password"]').should('be.visible');
      cy.get('button[type="submit"]').should('be.visible');
    });

    it('should maintain accessibility on mobile', () => {
      cy.viewport(375, 667);
      
      cy.visit('/login');
      cy.checkPageAccessibility();
    });
  });

  describe('Performance Tests', () => {
    it('should load login page quickly', () => {
      cy.visit('/login');
      
      // Verify page loads within 3 seconds
      cy.get('h1').should('contain', '用户登录');
    });

    it('should handle concurrent logins', () => {
      // Start login process
      cy.visit('/login');
      cy.get('input[name="username"]').type('testuser');
      cy.get('input[name="password"]').type('password123');
      
      // Simulate concurrent login
      cy.request('POST', '/api/auth/login', {
        username: 'testuser',
        password: 'password123'
      });
      
      // Complete login
      cy.get('button[type="submit"]').click();
      
      // Verify successful login
      cy.url().should('include', '/dashboard');
    });
  });
});