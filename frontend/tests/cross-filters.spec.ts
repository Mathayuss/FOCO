import { test, expect } from "./support"
import { tipoTeste } from "./fixtures/dashboard"

test("clique na barra aplica e remove a tipificacao em todos os paineis", async ({page,dashboardApi}) => {
  await page.goto("/")
  await expect(page.locator(".kpiValue").first()).toHaveText("12")
  const chart = page.locator(".panel").filter({hasText:"Principais tipificações"}).locator("canvas")
  await expect(chart).toBeVisible()
  const position = await chart.evaluate(element => ({x:155,y:(element.clientHeight + 8 - 20) / 2}))
  await expect.poll(() => chart.evaluate((element,point) => {
    const canvas = element as HTMLCanvasElement
    const scale = canvas.width / canvas.clientWidth
    const pixel = canvas.getContext("2d")!.getImageData(Math.floor(point.x * scale),Math.floor(point.y * scale),1,1).data
    return pixel[0] > 150 && pixel[1] < 100 && pixel[2] < 100 && pixel[3] > 0
  },position)).toBe(true)
  await chart.click({position})
  await expect(page.getByRole("combobox",{name:"Tipificação",exact:true})).toHaveValue(tipoTeste)
  await expect.poll(() => dashboardApi.requests[dashboardApi.requests.length - 1]?.searchParams.get("type")).toBe(tipoTeste)
  await expect(page.locator(".kpiValue").first()).toHaveText("4")
  await expect(page.locator(".topFilterChips")).toContainText(tipoTeste)
  await expect.poll(() => chart.evaluate((element,point) => {
    const canvas = element as HTMLCanvasElement
    const scale = canvas.width / canvas.clientWidth
    const pixel = canvas.getContext("2d")!.getImageData(Math.floor(point.x * scale),Math.floor(point.y * scale),1,1).data
    return pixel[0] > 200 && pixel[1] > 150 && pixel[2] < 100 && pixel[3] > 0
  },position)).toBe(true)
  await chart.click({position})
  await expect(page.getByRole("combobox",{name:"Tipificação",exact:true})).toHaveValue("")
  await expect(page.locator(".kpiValue").first()).toHaveText("12")
})
