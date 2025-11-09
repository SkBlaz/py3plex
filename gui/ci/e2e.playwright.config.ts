// Playwright configuration for e2e tests
// TODO: Complete implementation when running e2e tests

import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './frontend-tests',
  timeout: 30000,
  use: {
    baseURL: 'http://localhost:8080',
    trace: 'on-first-retry',
  },
  webServer: {
    command: 'cd .. && docker compose up',
    port: 8080,
    timeout: 120000,
    reuseExistingServer: true,
  },
});
