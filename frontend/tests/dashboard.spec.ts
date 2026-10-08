import { test, expect } from "./support"
import {
  dashboardFixture, municipioTeste, periodoTeste, subtipoTeste,
  tipoLongoTeste, tipoTeste, turnoTeste, unidadeTeste,
} from "./fixtures/dashboard"

async function openDashboard(page:import("@playwright/test").Page){
  await page.goto("/")
  await expect(page.locator(".kpiValue").first()).toHaveText("12")
}

test("carrega o dashboard consolidado e renderiza graficos", async ({page,dashboardApi}) => {
  await openDashboard(page)
  await expect(page.getByRole("heading",{name:"Visão Geral",exact:true})).toBeVisible()
  await expect(page.getByRole("status")).toHaveText("API e banco online")
  await expect(page.getByRole("combobox",{name:"Fonte",exact:true})).toContainText("nao operacional")
  await expect(page.locator("canvas")).toHaveCount(3)
  await expect.poll(() => page.locator("canvas").evaluateAll(canvases => canvases.every(canvas => {
    const element = canvas as HTMLCanvasElement
    const pixels = element.getContext("2d")?.getImageData(0,0,element.width,element.height).data
    return pixels?.some((value,index) => index % 4 === 3 && value > 0)
  }))).toBe(true)
  expect(dashboardApi.requests.every(url => url.pathname === "/api/v1/analytics/dashboard")).toBe(true)
})

test("envia os seis filtros e persiste ao navegar e recarregar", async ({page,dashboardApi}) => {
  await openDashboard(page)
  for(const [name,value] of [
    ["Período",periodoTeste],["Tipificação",tipoTeste],["Município",municipioTeste],
    ["Unidade",unidadeTeste],["Subtipo",subtipoTeste],["Turno",turnoTeste],
  ]){
    await page.getByRole("combobox",{name,exact:true}).selectOption(value)
  }
  const expected = {period:periodoTeste,type:tipoTeste,municipality:municipioTeste,
    unit:unidadeTeste,subtype:subtipoTeste,shift:turnoTeste}
  await expect.poll(() => {
    const params = dashboardApi.requests.at(-1)?.searchParams
    return Object.fromEntries(Object.keys(expected).map(key => [key,params?.get(key)]))
  }).toEqual(expected)
  await expect(page.locator(".kpiValue").first()).toHaveText("4")
  await page.getByRole("button",{name:"Evolução",exact:true}).click()
  await expect(page.getByRole("heading",{name:"Evolução",exact:true})).toBeVisible()
  await expect(page.locator(".kpiValue").first()).toHaveText("4")
  await page.reload()
  await expect(page.getByRole("heading",{name:"Evolução",exact:true})).toBeVisible()
  await expect(page.getByRole("combobox",{name:"Período",exact:true})).toHaveValue(periodoTeste)
  await expect(page.locator(".topFilterChips")).toContainText(municipioTeste)
  await expect(page.locator(".filterSummary")).toContainText("6 filtros ativos")
  await page.getByRole("button",{name:"Limpar filtros globais",exact:true}).click()
  await expect(page.locator(".kpiValue").first()).toHaveText("12")
  await expect(page.getByRole("combobox",{name:"Período",exact:true})).toHaveValue("all")
  await expect(page.locator(".topFilterChips button")).toHaveCount(0)
})

test("remove um filtro sem apagar os demais", async ({page,dashboardApi}) => {
  await openDashboard(page)
  await page.getByRole("combobox",{name:"Período",exact:true}).selectOption(periodoTeste)
  await page.getByRole("combobox",{name:"Município",exact:true}).selectOption(municipioTeste)
  await page.locator(".topFilterChips").getByRole("button",{name:`Remover filtro Município: ${municipioTeste}`,exact:true}).click()
  await expect.poll(() => dashboardApi.requests.at(-1)?.searchParams.get("municipality")).toBeNull()
  await expect(page.getByRole("combobox",{name:"Período",exact:true})).toHaveValue(periodoTeste)
  expect(dashboardApi.requests.at(-1)?.searchParams.get("period")).toBe(periodoTeste)
})

test("exibe a base comparada e a variacao do periodo", async ({page}) => {
  await openDashboard(page)
  await page.getByRole("combobox",{name:"Período",exact:true}).selectOption(periodoTeste)
  await expect(page.locator(".comparisonStrip")).toContainText("Fev/2025")
  await expect(page.locator(".comparisonStrip")).toContainText("Jan/2025")
  await expect(page.locator(".comparisonStrip")).toContainText("+100,0%")
})

test("identifica meses equivalentes quando o ano atual possui cobertura maior", async ({page,dashboardApi}) => {
  dashboardApi.respond = async route => {
    const data = dashboardFixture()
    data.overview.total = 16
    data.overview.delta_pct = 100
    data.overview.comparison = {
      available:true,current_label:"Jan-Jun/2026",baseline_label:"Jan-Jun/2025",
      current_total:12,baseline_total:6,delta_abs:6,delta_pct:100,
      reason:"Comparação limitada aos meses equivalentes com cobertura nos dois anos: Jan-Jun.",
      source_scope:"sejusp_importado",
    }
    await route.fulfill({json:data})
  }
  await page.goto("/")

  const comparison = page.locator(".comparisonStrip")
  await expect(comparison).toContainText("Recorte comparável")
  await expect(comparison).toContainText("Jan-Jun/2026")
  await expect(comparison).toContainText("Jan-Jun/2025")
  await expect(comparison).toContainText("meses equivalentes com cobertura nos dois anos")
  await expect(page.locator(".kpiGrid")).toContainText("16")
})

test("mostra base vazia sem inventar ocorrencias", async ({page,dashboardApi}) => {
  dashboardApi.respond = async route => { await route.fulfill({json:dashboardFixture(undefined,0)}) }
  await page.goto("/")
  await expect(page.locator(".kpiValue").first()).toHaveText("0")
  await expect(page.locator(".errorBox")).toHaveCount(0)
})

test("informa falha de rede sem manter numeros operacionais na tela", async ({page,dashboardApi}) => {
  dashboardApi.respond = async route => { await route.abort("connectionfailed") }
  await page.goto("/")
  await expect(page.locator(".errorBox")).toContainText("Não foi possível acessar a API")
  await expect(page.locator(".kpiGrid")).toHaveCount(0)
})

test("permite recuperar um filtro invalido persistido", async ({page,dashboardApi}) => {
  await page.addInitScript(() => localStorage.setItem("foco.globalFilters.v03",JSON.stringify({period:"ano-1900"})))
  dashboardApi.respond = async (route,params) => {
    if(params.get("period") === "ano-1900"){
      await route.fulfill({status:400,json:{detail:{code:"INVALID_FILTER",
        errors:[{field:"period",value:"ano-1900",allowed:["all"]}]}}})
    }else{
      await route.fulfill({json:dashboardFixture(params)})
    }
  }
  await page.goto("/")
  await expect(page.locator(".errorBox")).toContainText("Filtro inválido")
  await page.getByRole("button",{name:"Limpar filtros globais",exact:true}).click()
  await expect(page.locator(".kpiValue").first()).toHaveText("12")
  await expect(page.locator(".errorBox")).toHaveCount(0)
})

test("cancela requisicao substituida e ignora resposta atrasada", async ({page,dashboardApi}) => {
  await openDashboard(page)
  let release!:() => void
  const held = new Promise<void>(resolve => { release = resolve })
  dashboardApi.respond = async (route,params) => {
    if(params.get("period") === periodoTeste){
      await held
      await route.fulfill({json:dashboardFixture(params,888)}).catch(() => {})
    }else{
      await route.fulfill({json:dashboardFixture(params)})
    }
  }
  const pending = page.waitForRequest(request => new URL(request.url()).searchParams.get("period") === periodoTeste)
  const cancelled = page.waitForEvent("requestfailed",request => new URL(request.url()).searchParams.get("period") === periodoTeste)
  try{
    await page.getByRole("combobox",{name:"Período",exact:true}).selectOption(periodoTeste)
    await pending
    await page.getByRole("combobox",{name:"Período",exact:true}).selectOption("all")
    await expect(page.locator(".kpiValue").first()).toHaveText("12")
    release()
    await cancelled
    await expect(page.getByRole("combobox",{name:"Período",exact:true})).toHaveValue("all")
    await expect(page.locator(".kpiValue").first()).toHaveText("12")
  }finally{ release() }
})

test("tipificacoes extensas nao causam overflow horizontal", async ({page}) => {
  await openDashboard(page)
  await page.getByRole("combobox",{name:"Tipificação",exact:true}).selectOption(tipoLongoTeste)
  await expect(page.locator(".kpiValue").first()).toHaveText("4")
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  const select = page.getByRole("combobox",{name:"Tipificação",exact:true})
  const bounds = await select.boundingBox()
  expect(bounds?.width).toBeLessThanOrEqual(page.viewportSize()!.width)
})
