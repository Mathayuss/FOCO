import { test, expect } from "./support"
import { dashboardFixture, municipioTeste, tipoTeste } from "./fixtures/dashboard"

test("recorte vazio nao promove filtros selecionados a maior demanda", async ({page,dashboardApi}) => {
  dashboardApi.respond = async (route,params) => {
    await route.fulfill({json:dashboardFixture(params,0)})
  }
  await page.goto("/")
  const demand = page.locator(".kpi").filter({hasText:"Maior demanda"})
  await expect(page.locator(".kpiValue").first()).toHaveText("0")
  await expect(demand.locator(".kpiValue")).toHaveText("-")
  await expect(demand.locator(".kpiMeta")).toHaveText("sem dados")
  await page.getByRole("combobox",{name:"Tipificação",exact:true}).selectOption(tipoTeste)
  await page.getByRole("combobox",{name:"Município",exact:true}).selectOption(municipioTeste)
  await expect(page.locator(".topFilterChips")).toContainText(tipoTeste)
  await expect(page.locator(".topFilterChips")).toContainText(municipioTeste)
  await expect(demand.locator(".kpiValue")).toHaveText("-")
  await expect(demand.locator(".kpiMeta")).toHaveText("sem dados")
})

test("recorte com ocorrencias conserva maior demanda observada", async ({page}) => {
  await page.goto("/")
  const demand = page.locator(".kpi").filter({hasText:"Maior demanda"})
  await expect(demand.locator(".kpiValue")).toHaveText(tipoTeste)
  await expect(demand.locator(".kpiMeta")).toHaveText(municipioTeste)
})
