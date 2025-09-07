import { defineConfig } from 'cypress';
import { addCypressRelativePlugin } from '@cypress/webpack-preprocessor';

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    supportFile: 'cypress/support/e2e.ts',
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
    setupNodeEvents(on, config) {
      // This is required for the preprocessor to be able to generate JSON reports after each run, and more,
      // require('cypress-mochawesome-reporter/plugin')(on);
      on(
        'file:preprocessor',
        addCypressRelativePlugin(on, config)
      );
      return config;
    },
    viewportWidth: 1280,
    viewportHeight: 720,
    screenshotOnRunFailure: true,
    video: true,
    chromeWebSecurity: false,
    experimentalWebKitSupport: true,
    defaultCommandTimeout: 10000,
    requestTimeout: 10000,
    responseTimeout: 10000,
    pageLoadTimeout: 30000,
    testIsolation: true,
    numTestsKeptInMemory: 5,
    reporter: 'mochawesome',
    reporterOptions: {
      reportDir: 'cypress/reports',
      quite: false,
      overwrite: false,
      html: false,
      json: true,
    },
  },
  component: {
    devServer: {
      framework: 'react',
      bundler: 'webpack',
    },
    specPattern: 'cypress/component/**/*.{js,jsx,ts,tsx}',
    supportFile: 'cypress/support/component.ts',
    setupNodeEvents(on, config) {
      // This is required for the preprocessor to be able to generate JSON reports after each run, and more,
      // require('cypress-mochawesome-reporter/plugin')(on);
      on(
        'file:preprocessor',
        addCypressRelativePlugin(on, config)
      );
      return config;
    },
    viewportWidth: 1280,
    viewportHeight: 720,
  },
  env: {
    apiUrl: 'http://localhost:8001/api',
    tradingUrl: 'http://localhost:8002/api',
    strategyUrl: 'http://localhost:8003/api',
    adminUsername: 'admin',
    adminPassword: 'admin123',
    testUser: {
      username: 'testuser',
      password: 'testpass123',
      email: 'test@example.com'
    }
  },
});