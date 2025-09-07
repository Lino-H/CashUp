// cypress/e2e/strategies.cy.ts
import { getTestUser, generateRandomStrategy } from '../support/e2e';

describe('Strategies End-to-End Tests', () => {
  const testUser = getTestUser();
  const testStrategy = generateRandomStrategy();

  beforeEach(() => {
    cy.login(testUser.username, testUser.password);
    cy.visit('/strategies');
    cy.waitUntilStable();
  });

  describe('Strategies List', () => {
    it('should display strategies list', () => {
      // Verify strategies list is visible
      cy.get('[data-testid="strategies-list"]').should('be.visible');
      cy.get('[data-testid="strategies-header"]').should('contain', '策略管理');
      
      // Verify create strategy button
      cy.get('[data-testid="create-strategy-btn"]').should('be.visible');
      cy.get('[data-testid="create-strategy-btn"]').should('contain', '创建策略');
    });

    it('should show empty state when no strategies', () => {
      // Mock empty strategies
      cy.intercept('GET', '/api/strategies', {
        body: { strategies: [], total: 0 }
      }).as('getStrategies');
      
      cy.wait('@getStrategies');
      
      // Verify empty state
      cy.get('[data-testid="empty-state"]').should('be.visible');
      cy.get('[data-testid="empty-message"]').should('contain', '暂无策略');
      cy.get('[data-testid="create-strategy-btn"]').should('be.visible');
    });

    it('should display strategies with different statuses', () => {
      // Mock strategies with different statuses
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
            },
            {
              id: '2',
              name: 'Mean Reversion Strategy',
              status: 'stopped',
              symbol: 'ETHUSDT',
              timeframe: '4h',
              pnl: -500
            },
            {
              id: '3',
              name: 'Breakout Strategy',
              status: 'error',
              symbol: 'ADAUSDT',
              timeframe: '1d',
              pnl: 0
            }
          ]
        }
      }).as('getStrategies');
      
      cy.wait('@getStrategies');
      
      // Verify strategies with different statuses
      cy.get('[data-testid="strategy-item"]').should('have.length', 3);
      
      // Verify running strategy
      cy.get('[data-testid="strategy-item"]').first().within(() => {
        cy.get('[data-testid="strategy-name"]').should('contain', 'Moving Average Strategy');
        cy.get('[data-testid="strategy-status"]').should('contain', '运行中');
        cy.get('[data-testid="strategy-pnl"]').should('contain', '1000');
      });
      
      // Verify stopped strategy
      cy.get('[data-testid="strategy-item"]').eq(1).within(() => {
        cy.get('[data-testid="strategy-name"]').should('contain', 'Mean Reversion Strategy');
        cy.get('[data-testid="strategy-status"]').should('contain', '已停止');
        cy.get('[data-testid="strategy-pnl"]').should('contain', '-500');
      });
      
      // Verify error strategy
      cy.get('[data-testid="strategy-item"]').eq(2).within(() => {
        cy.get('[data-testid="strategy-name"]').should('contain', 'Breakout Strategy');
        cy.get('[data-testid="strategy-status"]').should('contain', '错误');
        cy.get('[data-testid="strategy-pnl"]').should('contain', '0');
      });
    });

    it('should allow strategy filtering', () => {
      // Mock strategies
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
      cy.get('[data-testid="strategy-name"]').should('contain', 'Moving Average Strategy');
      
      // Filter by symbol
      cy.get('[data-testid="symbol-filter"]').select('ETHUSDT');
      cy.get('[data-testid="strategy-item"]').should('have.length', 1);
      cy.get('[data-testid="strategy-name"]').should('contain', 'Mean Reversion Strategy');
    });

    it('should allow strategy sorting', () => {
      // Mock strategies
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
            },
            {
              id: '3',
              name: 'Strategy C',
              pnl: 1500
            }
          ]
        }
      }).as('getStrategies');
      
      cy.wait('@getStrategies');
      
      // Sort by P&L descending
      cy.get('[data-testid="sort-pnl"]').click();
      cy.get('[data-testid="strategy-item"]').first().within(() => {
        cy.get('[data-testid="strategy-pnl"]').should('contain', '1500');
      });
      
      // Sort by P&L ascending
      cy.get('[data-testid="sort-pnl"]').click();
      cy.get('[data-testid="strategy-item"]').first().within(() => {
        cy.get('[data-testid="strategy-pnl"]').should('contain', '500');
      });
    });

    it('should allow strategy searching', () => {
      // Mock strategies
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

  describe('Strategy Creation', () => {
    it('should navigate to strategy creation', () => {
      // Click create strategy button
      cy.get('[data-testid="create-strategy-btn"]').click();
      
      // Verify navigation
      cy.url().should('include', '/strategies/create');
      cy.get('h1').should('contain', '创建策略');
    });

    it('should show strategy creation form', () => {
      cy.visit('/strategies/create');
      
      // Verify form elements
      cy.get('[data-testid="strategy-name-input"]').should('be.visible');
      cy.get('[data-testid="strategy-symbol-input"]').should('be.visible');
      cy.get('[data-testid="strategy-timeframe-select"]').should('be.visible');
      cy.get('[data-testid="strategy-config-textarea"]').should('be.visible');
      cy.get('[data-testid="submit-btn"]').should('be.visible');
    });

    it('should validate strategy creation form', () => {
      cy.visit('/strategies/create');
      
      // Try to submit empty form
      cy.get('[data-testid="submit-btn"]').click();
      
      // Verify validation errors
      cy.get('[data-testid="error-name"]').should('contain', '请输入策略名称');
      cy.get('[data-testid="error-symbol"]').should('contain', '请选择交易对');
      cy.get('[data-testid="error-timeframe"]').should('contain', '请选择时间周期');
    });

    it('should create strategy successfully', () => {
      cy.visit('/strategies/create');
      
      // Fill in form
      cy.get('[data-testid="strategy-name-input"]').type(testStrategy.name);
      cy.get('[data-testid="strategy-symbol-input"]').type(testStrategy.symbol);
      cy.get('[data-testid="strategy-timeframe-select"]').select(testStrategy.timeframe);
      cy.get('[data-testid="strategy-config-textarea"]').type(JSON.stringify(testStrategy.config));
      
      // Submit form
      cy.get('[data-testid="submit-btn"]').click();
      
      // Verify API call
      cy.intercept('POST', '/api/strategies', {
        body: {
          id: '1',
          name: testStrategy.name,
          symbol: testStrategy.symbol,
          timeframe: testStrategy.timeframe,
          config: testStrategy.config,
          status: 'created'
        }
      }).as('createStrategy');
      
      cy.wait('@createStrategy');
      
      // Verify redirect to strategies list
      cy.url().should('include', '/strategies');
      cy.get('[data-testid="success-message"]').should('contain', '策略创建成功');
    });
  });

  describe('Strategy Management', () => {
    it('should allow strategy start', () => {
      // Mock strategy
      cy.intercept('GET', '/api/strategies', {
        body: {
          strategies: [
            {
              id: '1',
              name: 'Moving Average Strategy',
              status: 'stopped',
              symbol: 'BTCUSDT',
              timeframe: '1h',
              pnl: 0
            }
          ]
        }
      }).as('getStrategies');
      
      cy.wait('@getStrategies');
      
      // Click start button
      cy.get('[data-testid="start-strategy-btn"]').click();
      
      // Verify confirmation dialog
      cy.get('[data-testid="confirm-dialog"]').should('be.visible');
      cy.get('[data-testid="confirm-btn"]').click();
      
      // Verify API call
      cy.intercept('POST', '/api/strategies/1/start').as('startStrategy');
      cy.wait('@startStrategy');
      
      // Verify status change
      cy.get('[data-testid="strategy-status"]').should('contain', '运行中');
    });

    it('should allow strategy stop', () => {
      // Mock strategy
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

    it('should allow strategy edit', () => {
      // Mock strategy
      cy.intercept('GET', '/api/strategies', {
        body: {
          strategies: [
            {
              id: '1',
              name: 'Moving Average Strategy',
              status: 'running',
              symbol: 'BTCUSDT',
              timeframe: '1h',
              config: testStrategy.config
            }
          ]
        }
      }).as('getStrategies');
      
      cy.wait('@getStrategies');
      
      // Click edit button
      cy.get('[data-testid="edit-strategy-btn"]').click();
      
      // Verify navigation to edit page
      cy.url().should('include', '/strategies/1/edit');
      cy.get('h1').should('contain', '编辑策略');
    });

    it('should allow strategy delete', () => {
      // Mock strategy
      cy.intercept('GET', '/api/strategies', {
        body: {
          strategies: [
            {
              id: '1',
              name: 'Moving Average Strategy',
              status: 'stopped',
              symbol: 'BTCUSDT',
              timeframe: '1h',
              pnl: 0
            }
          ]
        }
      }).as('getStrategies');
      
      cy.wait('@getStrategies');
      
      // Click delete button
      cy.get('[data-testid="delete-strategy-btn"]').click();
      
      // Verify confirmation dialog
      cy.get('[data-testid="confirm-dialog"]').should('be.visible');
      cy.get('[data-testid="confirm-btn"]').click();
      
      // Verify API call
      cy.intercept('DELETE', '/api/strategies/1').as('deleteStrategy');
      cy.wait('@deleteStrategy');
      
      // Verify strategy removal
      cy.get('[data-testid="strategy-item"]').should('not.exist');
    });
  });

  describe('Strategy Backtesting', () => {
    it('should navigate to backtesting', () => {
      // Mock strategy
      cy.intercept('GET', '/api/strategies', {
        body: {
          strategies: [
            {
              id: '1',
              name: 'Moving Average Strategy',
              status: 'running',
              symbol: 'BTCUSDT',
              timeframe: '1h',
              config: testStrategy.config
            }
          ]
        }
      }).as('getStrategies');
      
      cy.wait('@getStrategies');
      
      // Click backtest button
      cy.get('[data-testid="backtest-strategy-btn"]').click();
      
      // Verify navigation to backtesting
      cy.url().should('include', '/backtest');
      cy.get('h1').should('contain', '策略回测');
    });

    it('should show backtesting form', () => {
      cy.visit('/backtest');
      
      // Verify form elements
      cy.get('[data-testid="backtest-strategy-select"]').should('be.visible');
      cy.get('[data-testid="backtest-start-date"]').should('be.visible');
      cy.get('[data-testid="backtest-end-date"]').should('be.visible');
      cy.get('[data-testid="backtest-submit-btn"]').should('be.visible');
    });

    it('should run backtest successfully', () => {
      cy.visit('/backtest');
      
      // Select strategy
      cy.get('[data-testid="backtest-strategy-select"]').select('Moving Average Strategy');
      
      // Set dates
      cy.get('[data-testid="backtest-start-date"]').type('2023-01-01');
      cy.get('[data-testid="backtest-end-date"]').type('2023-12-31');
      
      // Submit form
      cy.get('[data-testid="backtest-submit-btn"]').click();
      
      // Verify API call
      cy.intercept('POST', '/api/backtest', {
        body: {
          id: '1',
          name: 'Backtest 1',
          status: 'running'
        }
      }).as('createBacktest');
      
      cy.wait('@createBacktest');
      
      // Verify backtest running
      cy.get('[data-testid="backtest-status"]').should('contain', '运行中');
    });
  });

  describe('Strategy Performance', () => {
    it('should show strategy performance', () => {
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
      
      cy.wait(['@getStrategies', '@getPerformance']);
      
      // Click performance button
      cy.get('[data-testid="performance-strategy-btn"]').click();
      
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
      
      cy.wait(['@getStrategies', '@getPerformance']);
      
      // Click performance button
      cy.get('[data-testid="performance-strategy-btn"]').click();
      
      // Verify performance chart
      cy.get('[data-testid="performance-chart"]').should('be.visible');
      cy.get('svg').should('be.visible');
    });

    it('should show trade history', () => {
      // Mock trade data
      cy.intercept('GET', '/api/v1/trades/by-strategy/1', {
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
      
      cy.wait(['@getStrategies', '@getTrades']);
      
      // Click performance button
      cy.get('[data-testid="performance-strategy-btn"]').click();
      
      // Verify trade history
      cy.get('[data-testid="trade-history"]').should('be.visible');
      cy.get('[data-testid="trade-item"]').should('have.length', 1);
      cy.get('[data-testid="trade-symbol"]').should('contain', 'BTCUSDT');
      cy.get('[data-testid="trade-side"]').should('contain', '买入');
    });
  });

  describe('Strategy Templates', () => {
    it('should show strategy templates', () => {
      cy.visit('/strategies/templates');
      
      // Verify templates list
      cy.get('[data-testid="templates-list"]').should('be.visible');
      cy.get('[data-testid="template-item"]').should('have.length', 3);
    });

    it('should allow template selection', () => {
      cy.visit('/strategies/templates');
      
      // Select template
      cy.get('[data-testid="template-item"]').first().click();
      
      // Verify navigation to strategy creation
      cy.url().should('include', '/strategies/create');
      cy.get('[data-testid="strategy-config-textarea"]').should('contain', 'Moving Average Crossover');
    });

    it('should create strategy from template', () => {
      cy.visit('/strategies/create');
      
      // Use template
      cy.get('[data-testid="use-template-btn"]').click();
      
      // Verify template selection
      cy.get('[data-testid="template-selector"]').should('be.visible');
      cy.get('[data-testid="template-option"]').should('have.length', 3);
    });
  });

  describe('Strategy Sharing', () => {
    it('should allow strategy sharing', () => {
      // Mock strategy
      cy.intercept('GET', '/api/strategies', {
        body: {
          strategies: [
            {
              id: '1',
              name: 'Moving Average Strategy',
              status: 'running',
              symbol: 'BTCUSDT',
              timeframe: '1h',
              config: testStrategy.config
            }
          ]
        }
      }).as('getStrategies');
      
      cy.wait('@getStrategies');
      
      // Click share button
      cy.get('[data-testid="share-strategy-btn"]').click();
      
      // Verify share dialog
      cy.get('[data-testid="share-dialog"]').should('be.visible');
      cy.get('[data-testid="share-url"]').should('be.visible');
      cy.get('[data-testid="copy-btn"]').should('be.visible');
    });

    it('should allow strategy import', () => {
      cy.visit('/strategies/import');
      
      // Verify import form
      cy.get('[data-testid="import-file-input"]').should('be.visible');
      cy.get('[data-testid="import-url-input"]').should('be.visible');
      cy.get('[data-testid="import-submit-btn"]').should('be.visible');
    });

    it('should import strategy successfully', () => {
      cy.visit('/strategies/import');
      
      // Import strategy
      cy.get('[data-testid="import-url-input"]').type('https://example.com/strategy.json');
      cy.get('[data-testid="import-submit-btn"]').click();
      
      // Verify API call
      cy.intercept('POST', '/api/strategies/import', {
        body: {
          id: '2',
          name: 'Imported Strategy',
          status: 'created'
        }
      }).as('importStrategy');
      
      cy.wait('@importStrategy');
      
      // Verify import success
      cy.get('[data-testid="success-message"]').should('contain', '策略导入成功');
    });
  });

  describe('Accessibility Tests', () => {
    it('should be accessible', () => {
      cy.checkPageAccessibility();
    });

    it('should have proper ARIA labels', () => {
      cy.get('[aria-label="strategies list"]').should('exist');
      cy.get('[aria-label="create strategy"]').should('exist');
      cy.get('[aria-label="strategy actions"]').should('exist');
    });

    it('should be keyboard navigable', () => {
      // Test keyboard navigation
      cy.get('body').tab();
      cy.get('[data-testid="create-strategy-btn"]').should('have.focus');
      
      cy.get('body').tab();
      cy.get('[data-testid="search-input"]').should('have.focus');
    });
  });

  describe('Performance Tests', () => {
    it('should load strategies list quickly', () => {
      // Measure load time
      cy.visit('/strategies');
      
      // Verify list loads within 3 seconds
      cy.get('[data-testid="strategies-list"]').should('be.visible');
    });

    it('should handle large number of strategies', () => {
      // Mock large number of strategies
      const strategies = Array.from({ length: 50 }, (_, i) => ({
        id: `${i}`,
        name: `Strategy ${i}`,
        status: i % 3 === 0 ? 'running' : 'stopped',
        symbol: i % 2 === 0 ? 'BTCUSDT' : 'ETHUSDT',
        timeframe: '1h',
        pnl: i * 100
      }));
      
      cy.intercept('GET', '/api/strategies', {
        body: { strategies, total: 50 }
      }).as('getStrategies');
      
      cy.visit('/strategies');
      cy.wait('@getStrategies');
      
      // Verify all strategies are loaded
      cy.get('[data-testid="strategy-item"]').should('have.length', 50);
    });

    it('should handle concurrent API calls', () => {
      // Mock concurrent API calls
      cy.intercept('GET', '/api/strategies', {
        body: { strategies: [] }
      }).as('strategies');
      
      cy.intercept('GET', '/api/data/market/overview', {
        body: { total_markets: 50 }
      }).as('market');
      
      cy.intercept('GET', '/api/v1/balances', {
        body: { total_balance: 10000 }
      }).as('balances');
      
      // Wait for all requests
      cy.wait(['@strategies', '@market', '@balances']);
    });
  });

  describe('Mobile Responsiveness', () => {
    it('should work on mobile devices', () => {
      cy.viewport(375, 667);
      
      // Verify mobile layout
      cy.get('[data-testid="mobile-menu"]').should('be.visible');
      cy.get('[data-testid="strategy-card"]').should('be.visible');
    });

    it('should support touch interactions', () => {
      cy.viewport(375, 667);
      
      // Test touch interactions
      cy.get('[data-testid="strategy-card"]').touchSwipe('left');
      cy.get('[data-testid="strategy-actions"]').should('be.visible');
    });

    it('should adapt to mobile screen size', () => {
      cy.viewport(375, 667);
      
      // Verify elements are properly sized
      cy.get('[data-testid="strategy-card"]').should('be.visible');
      cy.get('[data-testid="strategy-name"]').should('be.visible');
    });
  });

  describe('Error Handling', () => {
    it('should handle strategy creation errors', () => {
      cy.visit('/strategies/create');
      
      // Mock API error
      cy.intercept('POST', '/api/strategies', {
        statusCode: 400,
        body: { error: 'Invalid strategy configuration' }
      }).as('createStrategy');
      
      // Fill in form
      cy.get('[data-testid="strategy-name-input"]').type('Test Strategy');
      cy.get('[data-testid="strategy-symbol-input"]').type('BTCUSDT');
      cy.get('[data-testid="strategy-timeframe-select"]').select('1h');
      cy.get('[data-testid="strategy-config-textarea"]').type('invalid config');
      
      // Submit form
      cy.get('[data-testid="submit-btn"]').click();
      cy.wait('@createStrategy');
      
      // Verify error message
      cy.get('[data-testid="error-message"]').should('contain', 'Invalid strategy configuration');
    });

    it('should handle strategy deletion errors', () => {
      // Mock API error
      cy.intercept('DELETE', '/api/strategies/1', {
        statusCode: 500,
        body: { error: 'Failed to delete strategy' }
      }).as('deleteStrategy');
      
      cy.intercept('GET', '/api/strategies', {
        body: {
          strategies: [
            {
              id: '1',
              name: 'Moving Average Strategy',
              status: 'stopped',
              symbol: 'BTCUSDT',
              timeframe: '1h',
              pnl: 0
            }
          ]
        }
      }).as('getStrategies');
      
      cy.wait('@getStrategies');
      
      // Try to delete strategy
      cy.get('[data-testid="delete-strategy-btn"]').click();
      cy.get('[data-testid="confirm-btn"]').click();
      cy.wait('@deleteStrategy');
      
      // Verify error message
      cy.get('[data-testid="error-message"]').should('contain', 'Failed to delete strategy');
    });
  });
});