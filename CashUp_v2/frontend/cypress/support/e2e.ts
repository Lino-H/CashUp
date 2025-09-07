// cypress/support/e2e.ts

import 'cypress-mochawesome-reporter/register';
import '@cypress/grep';

// Global test configuration
Cypress.config({
  defaultCommandTimeout: 10000,
  requestTimeout: 10000,
  responseTimeout: 10000,
  pageLoadTimeout: 30000,
  testIsolation: true,
});

// Custom commands
declare global {
  namespace Cypress {
    interface Chainable {
      login(username: string, password: string): Chainable<void>;
      logout(): Chainable<void>;
      waitForApi(endpoint: string): Chainable<void>;
      mockApi(endpoint: string, response: any): Chainable<void>;
      takeScreenshotOnFail(): Chainable<void>;
      clearCookiesAndLocalStorage(): Chainable<void>;
      checkPageAccessibility(): Chainable<void>;
      waitUntilStable(): Chainable<void>;
    }
  }
}

Cypress.Commands.add('login', (username: string, password: string) => {
  cy.session([username, password], () => {
    cy.visit('/login');
    
    // Wait for login form to load
    cy.get('input[name="username"]').should('be.visible');
    cy.get('input[name="password"]').should('be.visible');
    cy.get('button[type="submit"]').should('be.visible');
    
    // Fill in the form
    cy.get('input[name="username"]').type(username);
    cy.get('input[name="password"]').type(password);
    
    // Submit the form
    cy.get('button[type="submit"]').click();
    
    // Wait for dashboard to load
    cy.url().should('include', '/dashboard');
    cy.get('h1').should('contain', '欢迎回来');
  });
});

Cypress.Commands.add('logout', () => {
  cy.session([], () => {
    cy.visit('/dashboard');
    
    // Click logout button
    cy.get('button').contains('退出登录').click();
    
    // Wait for login page to load
    cy.url().should('include', '/login');
    cy.get('h1').should('contain', '用户登录');
  });
});

Cypress.Commands.add('waitForApi', (endpoint: string) => {
  cy.intercept('GET', endpoint).as('apiRequest');
  cy.wait('@apiRequest');
});

Cypress.Commands.add('mockApi', (endpoint: string, response: any) => {
  cy.intercept('GET', endpoint, {
    statusCode: 200,
    body: response,
  });
});

Cypress.Commands.add('takeScreenshotOnFail', () => {
  Cypress.on('fail', (error) => {
    const screenshotName = `failed-${Date.now()}`;
    cy.screenshot(screenshotName);
    throw error;
  });
});

Cypress.Commands.add('clearCookiesAndLocalStorage', () => {
  cy.clearCookies();
  cy.clearLocalStorage();
});

Cypress.Commands.add('checkPageAccessibility', () => {
  cy.injectAxe();
  cy.checkA11y();
});

Cypress.Commands.add('waitUntilStable', () => {
  cy.get('body').should('not.be.empty');
  cy.get('[data-testid="loading"]').should('not.exist');
});

// Custom utility functions
const getTestUser = () => {
  return Cypress.env('testUser');
};

const getAdminUser = () => {
  return {
    username: Cypress.env('adminUsername'),
    password: Cypress.env('adminPassword'),
  };
};

// Environment variables
const apiUrl = Cypress.env('apiUrl');
const tradingUrl = Cypress.env('tradingUrl');
const strategyUrl = Cypress.env('strategyUrl');

// Error handling
Cypress.on('uncaught:exception', (err, runnable) => {
  // Prevent test failures due to React 18 strict mode
  if (err.message.includes('Cannot read property') || err.message.includes('Cannot read properties')) {
    return false;
  }
  
  // Prevent test failures due to network errors
  if (err.message.includes('Network Error') || err.message.includes('Failed to fetch')) {
    return false;
  }
  
  // Allow other errors to fail tests
  return true;
});

// Test hooks
before(() => {
  // Global setup before all tests
  cy.clearCookiesAndLocalStorage();
  cy.visit('/');
  
  // Wait for application to load
  cy.waitUntilStable();
});

beforeEach(() => {
  // Setup before each test
  cy.clearCookiesAndLocalStorage();
  cy.viewport(1280, 720);
  
  // Mock API endpoints for consistent testing
  cy.mockApi(`${apiUrl}/auth/me`, {
    id: '1',
    username: 'testuser',
    email: 'test@example.com',
    created_at: '2023-01-01T00:00:00Z'
  });
  
  cy.mockApi(`${tradingUrl}/v1/balances`, {
    total_balance: 10000,
    available_balance: 8000,
    margin_balance: 2000,
    positions: []
  });
  
  cy.mockApi(`${strategyUrl}/strategies`, {
    strategies: [],
    total: 0,
    page: 1
  });
});

after(() => {
  // Cleanup after all tests
  cy.clearCookiesAndLocalStorage();
});

// Test data generators
const generateRandomUser = () => {
  const timestamp = Date.now();
  return {
    username: `user${timestamp}`,
    email: `user${timestamp}@example.com`,
    password: `password${timestamp}`,
  };
};

const generateRandomStrategy = () => {
  const timestamp = Date.now();
  return {
    name: `Strategy ${timestamp}`,
    symbol: 'BTCUSDT',
    timeframe: '1h',
    config: {
      indicators: [
        {
          type: 'sma',
          period: 20,
          color: '#00ff00'
        },
        {
          type: 'ema',
          period: 10,
          color: '#ff0000'
        }
      ],
      risk_management: {
        stop_loss: 2,
        take_profit: 5,
        max_position_size: 10
      }
    }
  };
};

// Export utility functions for use in tests
export {
  getTestUser,
  getAdminUser,
  generateRandomUser,
  generateRandomStrategy,
  apiUrl,
  tradingUrl,
  strategyUrl
};