import { test, expect } from "./support"
import { dashboardFixture, periodoTeste } from "./fixtures/dashboard"

test("ignora resposta antiga mesmo quando o transporte nao cancela", async ({page,dashboardApi}) => {
  // Simula um transporte que nao respeita o cancelamento, sem alterar a aplicacao.
  await page.addInitScript(() => { AbortController.prototype.abort = () => {} })
  await page.goto("/")
  await expect(page.locator(".kpiValue").first()).toHaveText("12")
  let release!:() => void
  const held = new Promise<void>(resolve => { release = resolve })
  dashboardApi.respond = async (route,params) => {
    if(params.get("period") === periodoTeste){
      await held
      await route.fulfill({json:dashboardFixture(params,888)})
    }else{
      await route.fulfill({json:dashboardFixture(params)})
    }
  }
  const pending = page.waitForRequest(request => new URL(request.url()).searchParams.get("period") === periodoTeste)
  try{
    await page.getByRole("combobox",{name:"Período",exact:true}).selectOption(periodoTeste)
    await pending
    await page.getByRole("combobox",{name:"Período",exact:true}).selectOption("all")
    await expect.poll(() => dashboardApi.requests[dashboardApi.requests.length - 1]?.searchParams.get("period")).toBe("all")
    const stale = page.waitForResponse(response => new URL(response.url()).searchParams.get("period") === periodoTeste)
    release()
    const response = await stale
    expect(response.status()).toBe(200)
    await response.finished()
    await page.evaluate(() => new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))))
    await expect(page.getByRole("combobox",{name:"Período",exact:true})).toHaveValue("all")
    await expect(page.locator(".kpiValue").first()).toHaveText("12")
    await expect(page.locator(".comparisonStrip")).not.toContainText("888")
  }finally{ release() }
})
