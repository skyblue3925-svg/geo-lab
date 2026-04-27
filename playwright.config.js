const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './projects/terrain-lab/tests/e2e',
  timeout: 120000,
  workers: 1,
  expect: {
    timeout: 20000,
  },
  use: {
    baseURL: 'http://127.0.0.1:8501',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  webServer: {
    command: "C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -ExecutionPolicy Bypass -File .\\run_geo_lab.ps1 -KillPortOwner",
    url: 'http://127.0.0.1:8501',
    reuseExistingServer: true,
    timeout: 120000,
  },
  projects: [
    {
      name: 'chromium',
      use: {
        browserName: 'chromium',
      },
    },
  ],
});
