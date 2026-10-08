import { defineConfig } from "@playwright/test"

const port = Number(process.env.FOCO_PORTA_TESTES || 4174)
if(!Number.isInteger(port) || port < 1024 || port > 65535){
  throw new Error("FOCO_PORTA_TESTES deve ser uma porta entre 1024 e 65535")
}
const baseURL = `http://127.0.0.1:${port}`

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  workers: 2,
  timeout: 30000,
  expect: {timeout: 10000},
  outputDir: "test-results",
  reporter: [["list"], ["html", {open:"never", outputFolder:"playwright-report"}]],
  use: {
    baseURL,
    browserName: "chromium",
    serviceWorkers: "block",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  projects: [
    {name:"desktop", use:{viewport:{width:1920,height:1080}}},
    {name:"notebook", use:{viewport:{width:1366,height:768}}},
    {name:"mobile", use:{viewport:{width:390,height:844},isMobile:true,hasTouch:true}},
  ],
  webServer: {
    command: `pnpm run dev --host 127.0.0.1 --port ${port} --strictPort`,
    url: baseURL,
    reuseExistingServer: false,
    timeout: 60000,
    env: {VITE_API_URL:`${baseURL}/api/v1`},
  },
})
