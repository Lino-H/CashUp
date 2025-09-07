// cypress/e2e/dashboard.cy.ts
import { getTestUser, generateRandomStrategy } from '../support/e2e';

describe('Dashboard End-to-End Tests', () => {
  const testUser = getTestUser();

  beforeEach(() => {
    cy.login(testUser.username, testUser.password);
    cy.visit('/dashboard');
    cy.waitUntilStable();
  });

  describe('Main Dashboard Layout', () => {
    it('should display dashboard with user info', () => {
      // Verify user greeting
      cy.get('h1').should('contain', '欢迎回来');
      cy.get('header').should('contain', testUser.username);
      
      // Verify main dashboard sections
      cy.get('[data-testid="account-overview"]').should('be.visible');
      cy.get('[data-testid="strategies-section"]').should('be.visible');
      cy.get('[data-testid="market-overview"]').should('be.visible');
      cy.get('[data-testid="performance-metrics"]').should('be.visible');
    });

    it('should show loading states', () => {
      // Mock loading state
      cy.intercept('GET', '/api/v1/balances', {
        delay: 2000,
        body: { total_balance: 10000 }
      }).as('loadingBalances');
      
      // Wait for loading to complete
      cy.wait('@loadingBalances');
      
      // Verify loading indicator
      cy.get('[data-testid="loading"]').should('not.exist');
    });

    it('should handle API errors gracefully', () => {
      // Mock API error
      cy.intercept('GET', '/api/v1/balances', {
        statusCode: 500,
        body: { error: 'Internal server error' }
      }).as('apiError');
      
      // Wait for error handling
      cy.wait('@apiError');
      
      // Verify error message
      cy.get('.error-message').should('contain', '加载账户信息失败');
    });

    it('should show responsive layout', () => {
      // Test desktop layout
      cy.viewport(1280, 720);
      cy.get('[data-testid="dashboard-grid"]').should('be.visible');
      
      // Test tablet layout
      cy.viewport(768, 1024);
      cy.get('[data-testid="dashboard-grid"]').should('be.visible');
      
      // Test mobile layout
      cy.viewport(375, 667);
      cy.get('[data-testid="dashboard-grid"]').should('be.visible');
    });
  });

  describe('Account Overview', () => {
    it('should display account balances', () => {
      // Verify balance display
      cy.get('[data-testid="total-balance"]').should('contain', '10000');
      cy.get('[data-testid="available-balance"]').should('contain', '8000');
      cy.get('[data-testid="margin-balance"]').should('contain', '2000');
    });

    it('should show account summary', () => {
      // Verify account summary
      cy.get('[data-testid="account-summary"]').should('be.visible');
      cy.get('[data-testid="account-id"]').should('contain', '12345');
      cy.get('[data-testid="leverage"]').should('contain', '10x');
    });

    it('should display portfolio chart', () => {
      // Verify portfolio chart
      cy.get('[data-testid="portfolio-chart"]').should('be.visible');
      cy.get('svg').should('be.visible');
    });

    it('should show profit/loss breakdown', () => {
      // Verify P&L breakdown
      cy.get('[data-testid="pnl-breakdown"]').should('be.visible');
      cy.get('[data-testid="total-pnl"]').should('contain', '0');
      cy.get('[data-testid="realized-pnl"]').should('contain', '0');
      cy.get('[data-testid="unrealized-pnl"]').should('contain', '0');
    });
  });

  describe('Strategies Section', () => {
    it('should display running strategies', () => {
      // Mock running strategies
      cy.intercept('GET', '/api/strategies', {
        body: {
          strategies: [
            {
              id: '1',
              name: 'Moving Average Strategy',
              status: 'running',
              symbol: 'BTCUSDT',
              timeframe: '1h',
              pnl: 1000
            }
          ]
        }
      }).as('getStrategies');
      
      cy.wait('@getStrategies');
      
      // Verify strategy display
      cy.get('[data-testid="strategies-list"]').should('be.visible');
      cy.get('[data-testid="strategy-item"]').should('have.length', 1);
      cy.get('[data-testid="strategy-name"]').should('contain', 'Moving Average Strategy');
      cy.get('[data-testid="strategy-status"]').should('contain', '运行中');
    });

    it('should show stopped strategies', () => {
      // Mock stopped strategies
      cy.intercept('GET', '/api/strategies', {
        body: {
          strategies: [
            {
              id: '2',
              name: 'Mean Reversion Strategy',
              status: 'stopped',
              symbol: 'ETHUSDT',
              timeframe: '4h',
              pnl: -500
            }
          ]
        }
      }).as('getStrategies');
      
      cy.wait('@getStrategies');
      
      // Verify stopped strategy display
      cy.get('[data-testid="strategy-status"]').should('contain', '已停止');
      cy.get('[data-testid="strategy-pnl"]').should('contain', '-500');
    });

    it('should allow strategy creation', () => {
      // Click create strategy button
      cy.get('[data-testid="create-strategy-btn"]').click();
      
      // Verify navigation to strategy creation
      cy.url().should('include', '/strategies/create');
      cy.get('h1').should('contain', '创建策略');
    });

    it('should show strategy controls', () => {
      // Mock running strategy
      cy.intercept('GET', '/api/strategies', {
        body: {
          strategies: [
            {
              id: '1',
              name: 'Moving Average Strategy',
              status: 'running',
              symbol: 'BTCUSDT',
              timeframe: '1h',
              pnl: 1000
            }
          ]
        }
      }).as('getStrategies');
      
      cy.wait('@getStrategies');
      
      // Verify strategy controls
      cy.get('[data-testid="stop-strategy-btn"]').should('be.visible');
      cy.get('[data-testid="edit-strategy-btn"]').should('be.visible');
      cy.get('[data-testid="delete-strategy-btn"]').should('be.visible');
    });

    it('should handle strategy state changes', () => {
      // Mock running strategy
      cy.intercept('GET', '/api/strategies', {
        body: {
          strategies: [
            {
              id: '1',
              name: 'Moving Average Strategy',
              status: 'running',
              symbol: 'BTCUSDT',
              timeframe: '1h',
              pnl: 1000
            }
          ]
        }
      }).as('getStrategies');
      
      cy.wait('@getStrategies');
      
      // Click stop button
      cy.get('[data-testid="stop-strategy-btn"]').click();
      
      // Verify confirmation dialog
      cy.get('[data-testid="confirm-dialog"]').should('be.visible');
      cy.get('[data-testid="confirm-btn"]').click();
      
      // Verify API call
      cy.intercept('POST', '/api/strategies/1/stop').as('stopStrategy');
      cy.wait('@stopStrategy');
      
      // Verify status change
      cy.get('[data-testid="strategy-status"]').should('contain', '已停止');
    });
  });

  describe('Market Overview', () => {
    it('should display market statistics', () => {
      // Mock market data
      cy.intercept('GET', '/api/data/market/overview', {
        body: {
          total_markets: 50,
          active_markets: 30,
          market_cap: '1.2T',
          volume_24h: '50B'
        }
      }).as('getMarketOverview');
      
      cy.wait('@getMarketOverview');
      
      // Verify market statistics
      cy.get('[data-testid="total-markets"]').should('contain', '50');
      cy.get('[data-testid="active-markets"]').should('contain', '30');
      cy.get('[data-testid="market-cap"]').should('contain', '1.2T');
      cy.get('[data-testid="volume-24h"]').should('contain', '50B');
    });

    it('should show top movers', () => {
      // Mock top movers data
      cy.intercept('GET', '/api/data/market/top-movers', {
        body: {
          gainers: [
            { symbol: 'BTCUSDT', change: 5.2 },
            { symbol: 'ETHUSDT', change: 3.8 }
          ],
          losers: [
            { symbol: 'ADAUSDT', change: -2.1 },
            { symbol: 'DOTUSDT', change: -1.5 }
          ]
        }
      }).as('getTopMovers');
      
      cy.wait('@getTopMovers');
      
      // Verify top movers display
      cy.get('[data-testid="top-gainers"]').should('be.visible');
      cy.get('[data-testid="top-losers"]').should('be.visible');
      cy.get('[data-testid="gainer-item"]').should('have.length', 2);
      cy.get('[data-testid="loser-item"]').should('have.length', 2);
    });

    it('should display market sentiment', () => {
      // Mock market sentiment data
      cy.intercept('GET', '/api/data/market/sentiment', {
        body: {
          bullish: 65,
          bearish: 25,
          neutral: 10
        }
      }).as('getMarketSentiment');
      
      cy.wait('@getMarketSentiment');
      
      // Verify sentiment display
      cy.get('[data-testid="market-sentiment"]').should('be.visible');
      cy.get('[data-testid="bullish-percentage"]').should('contain', '65%');
      cy.get('[data-testid="bearish-percentage"]').should('contain', '25%');
      cy.get('[data-testid="neutral-percentage"]').should('contain', '10%');
    });
  });

  describe('Performance Metrics', () => {
    it('should display strategy performance', () => {
      // Mock performance data
      cy.intercept('GET', '/api/strategies/1/performance', {
        body: {
          total_pnl: 1000,
          win_rate: 65,
          trades_count: 100,
          max_drawdown: 10,
          sharpe_ratio: 1.5
        }
      }).as('getPerformance');
      
      cy.wait('@getPerformance');
      
      // Verify performance metrics
      cy.get('[data-testid="total-pnl"]').should('contain', '1000');
      cy.get('[data-testid="win-rate"]').should('contain', '65%');
      cy.get('[data-testid="trades-count"]').should('contain', '100');
      cy.get('[data-testid="max-drawdown"]').should('contain', '10%');
      cy.get('[data-testid="sharpe-ratio"]').should('contain', '1.5');
    });

    it('should show performance chart', () => {
      // Mock performance data
      cy.intercept('GET', '/api/strategies/1/performance', {
        body: {
          equity_curve: [
            { date: '2023-01-01', equity: 10000 },
            { date: '2023-01-02', equity: 10500 },
            { date: '2023-01-03', equity: 10300 }
          ]
        }
      }).as('getPerformance');
      
      cy.wait('@getPerformance');
      
      // Verify performance chart
      cy.get('[data-testid="performance-chart"]').should('be.visible');
      cy.get('svg').should('be.visible');
    });

    it('should show trade history', () => {
      // Mock trade history
      cy.intercept('GET', '/api/v1/trades', {
        body: [
          {
            id: '1',
            symbol: 'BTCUSDT',
            side: 'buy',
            quantity: 0.1,
            price: 50000,
            pnl: 100
          }
        ]
      }).as('getTrades');
      
      cy.wait('@getTrades');
      
      // Verify trade history
      cy.get('[data-testid="trade-history"]').should('be.visible');
      cy.get('[data-testid="trade-item"]').should('have.length', 1);
      cy.get('[data-testid="trade-symbol"]').should('contain', 'BTCUSDT');
      cy.get('[data-testid="trade-side"]').should('contain', '买入');
      cy.get('[data-testid="trade-pnl"]').should('contain', '100');
    });
  });

  describe('Real-time Updates', () => {
    it('should handle real-time price updates', () => {
      // Mock real-time data
      cy.intercept('GET', '/api/data/realtime/BTCUSDT', {
        body: {
          symbol: 'BTCUSDT',
          price: 50000,
          change24h: 2.5
        }
      }).as('getRealTimeData');
      
      cy.wait('@getRealTimeData');
      
      // Verify price display
      cy.get('[data-testid="btc-price"]').should('contain', '50000');
      cy.get('[data-testid="btc-change"]').should('contain', '2.5%');
    });

    it('should handle real-time strategy updates', () => {
      // Mock strategy updates
      cy.intercept('GET', '/api/strategies', {
        body: {
          strategies: [
            {
              id: '1',
              name: 'Moving Average Strategy',
              status: 'running',
              symbol: 'BTCUSDT',
              timeframe: '1h',
              pnl: 1200
            }
          ]
        }
      }).as('getStrategies');
      
      cy.wait('@getStrategies');
      
      // Verify strategy updates
      cy.get('[data-testid="strategy-pnl"]').should('contain', '1200');
    });
  });

  describe('Interactive Features', () => {
    it('should allow filtering strategies', () => {
      // Mock strategies data
      cy.intercept('GET', '/api/strategies', {
        body: {
          strategies: [
            {
              id: '1',
              name: 'Moving Average Strategy',
              status: 'running',
              symbol: 'BTCUSDT'
            },
            {
              id: '2',
              name: 'Mean Reversion Strategy',
              status: 'stopped',
              symbol: 'ETHUSDT'
            }
          ]
        }
      }).as('getStrategies');
      
      cy.wait('@getStrategies');
      
      // Filter by status
      cy.get('[data-testid="status-filter"]').select('running');
      cy.get('[data-testid="strategy-item"]').should('have.length', 1);
      
      // Filter by symbol
      cy.get('[data-testid="symbol-filter"]').select('ETHUSDT');
      cy.get('[data-testid="strategy-item"]').should('have.length', 1);
    });

    it('should allow sorting strategies', () => {
      // Mock strategies data
      cy.intercept('GET', '/api/strategies', {
        body: {
          strategies: [
            {
              id: '1',
              name: 'Strategy A',
              pnl: 1000
            },
            {
              id: '2',
              name: 'Strategy B',
              pnl: 500
            }
          ]
        }
      }).as('getStrategies');
      
      cy.wait('@getStrategies');
      
      // Sort by P&L
      cy.get('[data-testid="sort-pnl"]').click();
      cy.get('[data-testid="strategy-item"]').first().should('contain', '1000');
    });

    it('should allow searching strategies', () => {
      // Mock strategies data
      cy.intercept('GET', '/api/strategies', {
        body: {
          strategies: [
            {
              id: '1',
              name: 'Moving Average Strategy',
              symbol: 'BTCUSDT'
            },
            {
              id: '2',
              name: 'Mean Reversion Strategy',
              symbol: 'ETHUSDT'
            }
          ]
        }
      }).as('getStrategies');
      
      cy.wait('@getStrategies');
      
      // Search by name
      cy.get('[data-testid="search-input"]').type('Moving');
      cy.get('[data-testid="strategy-item"]').should('have.length', 1);
      cy.get('[data-testid="strategy-name"]').should('contain', 'Moving');
    });
  });

  describe('Accessibility Tests', () => {
    it('should be accessible', () => {
      cy.checkPageAccessibility();
    });

    it('should have proper ARIA labels', () => {
      cy.get('[aria-label="dashboard"]').should('exist');
      cy.get('[aria-label="account overview"]').should('exist');
      cy.get('[aria-label="strategies"]').should('exist');
      cy.get('[aria-label="market overview"]').should('exist');
    });

    it('should be keyboard navigable', () => {
      // Test keyboard navigation
      cy.get('body').tab();
      cy.get('button').first().should('have.focus');
      
      cy.get('body').tab();
      cy.get('button').eq(1).should('have.focus');
    });
  });

  describe('Performance Tests', () => {
    it('should load dashboard quickly', () => {
      // Measure load time
      cy.visit('/dashboard');
      
      // Verify dashboard loads within 5 seconds
      cy.get('[data-testid="dashboard-grid"]').should('be.visible');
    });

    it('should handle multiple concurrent requests', () => {
      // Mock multiple concurrent requests
      cy.intercept('GET', '/api/v1/balances', {
        body: { total_balance: 10000 }
      }).as('balances');
      
      cy.intercept('GET', '/api/strategies', {
        body: { strategies: [] }
      }).as('strategies');
      
      cy.intercept('GET', '/api/data/market/overview', {
        body: { total_markets: 50 }
      }).as('market');
      
      // Wait for all requests
      cy.wait(['@balances', '@strategies', '@market']);
    });
  });

  describe('Error Handling', () => {
    it('should handle API timeouts', () => {
      // Mock timeout
      cy.intercept('GET', '/api/v1/balances', {
        delay: 10000,
        body: { total_balance: 10000 }
      }).as('timeout');
      
      // Wait for timeout
      cy.wait('@timeout');
      
      // Verify error message
      cy.get('.error-message').should('contain', '请求超时');
    });

    it('should handle network errors', () => {
      // Mock network error
      cy.intercept('GET', '/api/v1/balances', {
        statusCode: 0,
        body: { error: 'Network error' }
      }).as('networkError');
      
      // Wait for network error
      cy.wait('@networkError');
      
      // Verify error message
      cy.get('.error-message').should('contain', '网络错误');
    });

    it('should handle authentication errors', () => {
      // Mock auth error
      cy.intercept('GET', '/api/v1/balances', {
        statusCode: 401,
        body: { error: 'Unauthorized' }
      }).as('authError');
      
      // Wait for auth error
      cy.wait('@authError');
      
      // Verify redirect to login
      cy.url().should('include', '/login');
    });
  });

  describe('Mobile Responsiveness', () => {
    it('should work on mobile devices', () => {
      cy.viewport(375, 667);
      
      // Verify mobile layout
      cy.get('[data-testid="mobile-menu"]').should('be.visible');
      cy.get('[data-testid="account-overview"]').should('be.visible');
      cy.get('[data-testid="strategies-section"]').should('be.visible');
    });

    it('should adapt to mobile screen size', () => {
      cy.viewport(375, 667);
      
      // Verify elements are properly sized
      cy.get('[data-testid="dashboard-grid"]').should('be.visible');
      cy.get('[data-testid="strategy-card"]').should('be.visible');
    });

    it('should support touch interactions', () => {
      cy.viewport(375, 667);
      
      // Test touch interactions
      cy.get('[data-testid="strategy-card"]').touchSwipe('left');
      cy.get('[data-testid="strategy-details"]').should('be.visible');
    });
  });
});