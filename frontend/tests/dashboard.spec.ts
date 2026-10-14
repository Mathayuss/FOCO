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
  await expect(page.getByRole("combobox",{name:"Fonte",exact:true})).toHaveCount(0)
  await expect(page.locator(".filterHeading")).toContainText("SEJUSP importado")
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
  await expect(page.locator(".comparisonStrip")).toContainText("Fev/2025")
  await expect(page.locator(".comparisonStrip")).toContainText("Fev/2024")

  await page.getByRole("button",{name:"Tipificação",exact:true}).click()
  const typeRow=page.locator(".dataTable tbody tr").filter({hasText:tipoTeste})
  await expect(typeRow).toContainText("4")
  await expect(typeRow).toContainText("100,0%")

  await page.getByRole("button",{name:"Temporal",exact:true}).click()
  await expect(page.locator(".kpiGrid")).toContainText("14h")
  await expect(page.locator(".kpiGrid")).toContainText("1")

  await page.getByRole("button",{name:"Evolução",exact:true}).click()
  await expect(page.getByRole("heading",{name:"Evolução",exact:true})).toBeVisible()
  await expect(page.locator(".kpiValue").first()).toHaveText("4")
  await expect(page.locator(".kpiGrid")).toContainText("Fev/2024")
  await expect(page.locator(".kpiGrid")).toContainText("2")
  await page.reload()
  await expect(page.getByRole("heading",{name:"Evolução",exact:true})).toBeVisible()
  await expect(page.getByRole("combobox",{name:"Período",exact:true})).toHaveValue(periodoTeste)
  await expect(page.locator(".topFilterChips")).toContainText(municipioTeste)
  await expect(page.locator(".topFilterChips button")).toHaveCount(6)
  await page.getByRole("button",{name:"Limpar filtros globais",exact:true}).click()
  await expect(page.locator(".kpiValue").first()).toHaveText("12")
  await expect(page.getByRole("combobox",{name:"Período",exact:true})).toHaveValue("all")
  await expect(page.locator(".topFilterChips button")).toHaveCount(0)
})

test("mantem a area superior compacta e sem informacoes repetidas", async ({page},testInfo) => {
  await openDashboard(page)

  await expect(page.locator(".filterSummary")).toHaveCount(0)
  await expect(page.locator(".activeFilters")).toHaveCount(0)
  await expect(page.locator(".scopeNote")).toHaveCount(0)
  await expect(page.locator(".overviewHead")).toHaveCount(0)
  await expect(page.locator(".pageHead .eyebrow")).toHaveCount(0)
  await expect(page.locator(".pageHead .badge")).toHaveCount(0)
  await expect(page.locator(".topbar").getByRole("heading",{name:"Visão Geral",exact:true})).toBeVisible()
  await expect(page.locator(".topbarTitle")).toContainText("Ocorrências e indicadores operacionais consolidados")
  await expect(page.locator(".overviewKpis .kpi")).toHaveCount(3)
  await expect(page.locator(".overviewKpis")).not.toContainText("Cobertura SLA")
  await expect(page.locator(".overviewKpis")).not.toContainText("Variação")

  const topbarHeight=await page.locator(".topbar").evaluate(element=>element.getBoundingClientRect().height)
  expect(topbarHeight).toBeLessThanOrEqual(56)
  if(testInfo.project.name === "desktop"){
    const resultsTop=await page.locator(".comparisonStrip").evaluate(element=>element.getBoundingClientRect().top)
    expect(resultsTop).toBeLessThan(330)
  }
})

test("remove um filtro sem apagar os demais", async ({page,dashboardApi},testInfo) => {
  await openDashboard(page)
  await page.getByRole("combobox",{name:"Período",exact:true}).selectOption(periodoTeste)
  await page.getByRole("combobox",{name:"Município",exact:true}).selectOption(municipioTeste)
  if(testInfo.project.name === "mobile"){
    await page.getByRole("combobox",{name:"Município",exact:true}).selectOption("")
  }else{
    await page.locator(".topFilterChips").getByRole("button",{name:`Remover filtro Município: ${municipioTeste}`,exact:true}).click()
  }
  await expect.poll(() => dashboardApi.requests.at(-1)?.searchParams.get("municipality")).toBeNull()
  await expect(page.getByRole("combobox",{name:"Período",exact:true})).toHaveValue(periodoTeste)
  expect(dashboardApi.requests.at(-1)?.searchParams.get("period")).toBe(periodoTeste)
})

test("exibe a base comparada e a variacao do periodo", async ({page}) => {
  await openDashboard(page)
  await page.getByRole("combobox",{name:"Período",exact:true}).selectOption(periodoTeste)
  await expect(page.locator(".comparisonStrip")).toContainText("Fev/2025")
  await expect(page.locator(".comparisonStrip")).toContainText("Fev/2024")
  await expect(page.locator(".comparisonStrip")).toContainText("+100,0%")
})

test("compara o ano selecionado com o mesmo periodo do ano anterior", async ({page,dashboardApi}) => {
  await openDashboard(page)
  await page.getByRole("combobox",{name:"Período",exact:true}).selectOption("ano-2026")

  await expect.poll(()=>dashboardApi.requests.at(-1)?.searchParams.get("period")).toBe("ano-2026")
  const comparison=page.locator(".comparisonStrip")
  await expect(comparison).toContainText("2026")
  await expect(comparison).toContainText("2025")
})

test("aplica intervalo personalizado e compara as mesmas datas do ano anterior", async ({page,dashboardApi}) => {
  await openDashboard(page)
  await page.getByRole("button",{name:"Definir intervalo personalizado"}).click()
  await page.getByLabel("Data inicial").fill("2026-01-15")
  await page.getByLabel("Data final").fill("2026-02-10")
  await page.getByRole("button",{name:"Aplicar período"}).click()

  await expect.poll(()=>dashboardApi.requests.at(-1)?.searchParams.get("period")).toBe("faixa-2026-01-15--2026-02-10")
  const comparison=page.locator(".comparisonStrip")
  await expect(comparison).toContainText("15/01/2026 a 10/02/2026")
  await expect(comparison).toContainText("15/01/2025 a 10/02/2025")
})

test("mapa exibe detalhes e aplica filtro municipal", async ({page,dashboardApi}) => {
  await openDashboard(page)
  const marker=page.locator(".leaflet-interactive").first()
  await marker.hover()
  await expect(page.locator(".leaflet-tooltip")).toContainText(municipioTeste)
  await expect(page.locator(".leaflet-tooltip")).toContainText("12 ocorrências")
  await marker.click()
  await expect.poll(()=>dashboardApi.requests.at(-1)?.searchParams.get("municipality")).toBe(municipioTeste)
  await expect(page.getByRole("button",{name:"Limpar município selecionado"})).toBeVisible()
})

test("sair do mapa durante o enquadramento nao gera erro Leaflet", async ({page,dashboardApi}) => {
  const pageErrors:string[]=[]
  page.on("pageerror",error=>pageErrors.push(error.message))
  dashboardApi.respond=async (route,params) => {
    const data=dashboardFixture(params)
    data.cities.items=[
      {nome:"NORTE TESTE",total:7,pct:35,lat:-15.5,lon:-58.2},
      {nome:"CENTRO TESTE",total:8,pct:40,lat:-20.4,lon:-54.6},
      {nome:"SUL TESTE",total:5,pct:25,lat:-24.8,lon:-51.1},
    ]
    await route.fulfill({json:data})
  }

  await openDashboard(page)
  await page.getByRole("button",{name:"Território",exact:true}).click()
  await expect(page.locator(".leaflet-interactive")).toHaveCount(3)
  await page.locator(".leaflet-interactive").first().click()
  await expect(page.getByRole("button",{name:"Limpar município selecionado"})).toBeVisible()
  await page.getByRole("button",{name:"SLA",exact:true}).click()
  await expect(page.getByRole("heading",{name:"SLA",exact:true})).toBeVisible()
  await page.waitForTimeout(700)
  expect(pageErrors).toEqual([])
})

test("textos operacionais essenciais mantem tamanho legivel", async ({page}) => {
  await openDashboard(page)
  for(const selector of [".filters select",".kpiMeta",".panel>header b"]){
    const size=await page.locator(selector).first().evaluate(element=>Number.parseFloat(getComputedStyle(element).fontSize))
    expect(size,selector).toBeGreaterThanOrEqual(10)
  }
  await page.getByRole("button",{name:"Tipificação",exact:true}).click()
  const tableSize=await page.locator(".dataTable").evaluate(element=>Number.parseFloat(getComputedStyle(element).fontSize))
  expect(tableSize,".dataTable").toBeGreaterThanOrEqual(10)
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
