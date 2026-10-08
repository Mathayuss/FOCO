import { test, expect } from "./support"
import { dashboardFixture, periodoTeste, tipoLongoTeste, tipoTeste, unidadeTeste } from "./fixtures/dashboard"

test("tipificacao pode ser aplicada e removida por teclado na tabela", async ({page,dashboardApi}) => {
  await page.goto("/")
  await page.getByRole("button",{name:"Tipificação",exact:true}).click()
  const action = page.getByRole("button",{name:`Filtrar Tipificação: ${tipoTeste}`,exact:true})
  await expect(action).toBeVisible()
  await action.focus()
  await page.keyboard.press("Enter")
  await expect(page.getByRole("combobox",{name:"Tipificação",exact:true})).toHaveValue(tipoTeste)
  await expect.poll(() => dashboardApi.requests.at(-1)?.searchParams.get("type")).toBe(tipoTeste)
  await action.focus()
  await page.keyboard.press("Space")
  await expect(page.getByRole("combobox",{name:"Tipificação",exact:true})).toHaveValue("")
  await expect.poll(() => dashboardApi.requests.at(-1)?.searchParams.get("type")).toBeNull()
})

test("unidade pode ser filtrada por teclado sem perder o periodo", async ({page,dashboardApi}) => {
  await page.goto("/")
  await page.getByRole("combobox",{name:"Período",exact:true}).selectOption(periodoTeste)
  await page.getByRole("button",{name:"Unidades",exact:true}).click()
  const action = page.getByRole("button",{name:`Filtrar Unidade: ${unidadeTeste}`,exact:true})
  await expect(action).toBeVisible()
  await action.focus()
  await page.keyboard.press("Enter")
  await expect(page.getByRole("combobox",{name:"Período",exact:true})).toHaveValue(periodoTeste)
  await expect(page.locator(".topFilterChips")).toContainText(unidadeTeste)
  await expect.poll(() => dashboardApi.requests.at(-1)?.searchParams.get("unit")).toBe(unidadeTeste)
  await expect.poll(() => dashboardApi.requests.at(-1)?.searchParams.get("period")).toBe(periodoTeste)
})

test("clique na linha continua aplicando a tipificacao uma vez", async ({page,dashboardApi}) => {
  await page.goto("/")
  await page.getByRole("button",{name:"Tipificação",exact:true}).click()
  const row = page.locator(".dataTable tbody tr").filter({hasText:tipoTeste})
  await expect(row).toBeVisible()
  await row.locator("td").nth(1).click()
  await expect(page.getByRole("combobox",{name:"Tipificação",exact:true})).toHaveValue(tipoTeste)
  await expect.poll(() => dashboardApi.requests.at(-1)?.searchParams.get("type")).toBe(tipoTeste)
})

test("nome longo da tipificacao cabe na tabela sem overflow horizontal", async ({page,dashboardApi}) => {
  dashboardApi.respond = async (route,params) => {
    const data = dashboardFixture(params)
    data.types.items = [{nome:tipoLongoTeste,total:data.overview.total,pct:100}]
    await route.fulfill({json:data})
  }
  await page.goto("/")
  await page.getByRole("button",{name:"Tipificação",exact:true}).click()
  const action = page.getByRole("button",{name:`Filtrar Tipificação: ${tipoLongoTeste}`,exact:true})
  await expect(action).toBeVisible()
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  const bounds = await action.boundingBox()
  expect(bounds).not.toBeNull()
  expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(page.viewportSize()!.width)
})
