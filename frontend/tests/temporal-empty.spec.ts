import { test, expect } from "./support"
import { dashboardFixture } from "./fixtures/dashboard"

test("recorte sem horarios registrados nao inventa pico as 00h", async ({page,dashboardApi}) => {
  dashboardApi.respond = async route => {
    await route.fulfill({json:dashboardFixture(undefined,0)})
  }
  await page.goto("/")
  await page.getByRole("button",{name:"Temporal",exact:true}).click()
  const peak = page.locator(".kpi").filter({hasText:"Pico horário"})
  await expect(peak.locator(".kpiValue")).toHaveText("sem dados")
  await expect(peak.locator(".kpiMeta")).toHaveText("sem horário registrado")
  await expect(peak).not.toContainText("00h")
})

test("recorte com horarios conserva o pico observado", async ({page}) => {
  await page.goto("/")
  await page.getByRole("button",{name:"Temporal",exact:true}).click()
  const peak = page.locator(".kpi").filter({hasText:"Pico horário"})
  await expect(peak.locator(".kpiValue")).toHaveText("14h")
  await expect(peak.locator(".kpiMeta")).toHaveText("12 ocorrências")
})
