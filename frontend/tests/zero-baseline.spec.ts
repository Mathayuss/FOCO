import { test, expect } from "./support"
import { dashboardFixture, periodoTeste } from "./fixtures/dashboard"

const reason = "A base anterior não possui ocorrências para calcular a variação percentual."

test("base anterior zerada nao apresenta percentual como variacao valida", async ({page,dashboardApi}) => {
  dashboardApi.respond = async (route,params) => {
    const data = dashboardFixture(params,0)
    if(params.get("period") === periodoTeste){
      data.overview.delta_pct = null
      data.overview.comparison = {
        ...data.overview.comparison,
        available:true,
        current_total:0,baseline_total:0,delta_abs:0,delta_pct:null,
        reason,
      }
      data.monthly.comparison = [{current_month:"Fev/2025",baseline_month:"Jan/2025",
        current:0,baseline:0,delta:0}]
    }
    await route.fulfill({json:data})
  }
  await page.goto("/")
  await page.getByRole("combobox",{name:"Período",exact:true}).selectOption(periodoTeste)
  const variation = page.locator(".kpi").filter({hasText:"Variação"})
  await expect(variation.locator(".kpiValue")).toHaveText("indisponível")
  await expect(variation.locator(".kpiMeta")).toHaveText("base anterior: 0 ocorrências")
  await expect(page.locator(".comparisonStrip .reason")).toContainText(reason)
  await expect(page.locator(".comparisonStrip .muted")).toBeVisible()
  await page.getByRole("button",{name:"Evolução",exact:true}).click()
  await expect(page.getByRole("heading",{name:"Evolução",exact:true})).toBeVisible()
  await expect(variation.locator(".kpiValue")).toHaveText("indisponível")
  await expect(variation.locator(".kpiMeta")).toHaveText("base anterior: 0 ocorrências")
})
