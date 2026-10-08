import { test, expect } from "./support"
import { dashboardFixture, periodoTeste, tipoTeste, municipioTeste, unidadeTeste, subtipoTeste, turnoTeste } from "./fixtures/dashboard"

test("carga inicial nao apresenta indicadores como dados conhecidos", async ({page,dashboardApi}) => {
  let release!:() => void
  const held = new Promise<void>(resolve => { release = resolve })
  dashboardApi.respond = async route => {
    await held
    await route.fulfill({json:dashboardFixture()}).catch(() => {})
  }
  try{
    await page.goto("/")
    await expect.poll(() => dashboardApi.requests.length).toBeGreaterThan(0)
    await expect(page.getByRole("heading",{name:"Visão Geral",exact:true})).toBeVisible()
    await expect(page.getByRole("combobox",{name:"Período",exact:true})).toBeVisible()
    await expect(page.locator(".kpiGrid")).toHaveCount(0)
    await expect(page.locator(".comparisonStrip")).toHaveCount(0)
    await expect(page.locator(".coveragePanel")).toHaveCount(0)
    await expect(page.locator("canvas")).toHaveCount(0)
    release()
    await expect(page.locator(".kpiValue").first()).toHaveText("12")
  }finally{ release() }
})

for(const name of ["Visão Geral","Evolução","Tipificação","Temporal","Território","Unidades"]){
  test(`${name}: resultados anteriores desaparecem ao trocar o periodo`, async ({page,dashboardApi}) => {
    await page.goto("/")
    await expect(page.locator(".kpiValue").first()).toHaveText("12")
    if(name !== "Visão Geral"){
      await page.getByRole("button",{name,exact:true}).click()
      await expect(page.getByRole("heading",{name,exact:true})).toBeVisible()
    }
    let release!:() => void
    const held = new Promise<void>(resolve => { release = resolve })
    dashboardApi.respond = async (route,params) => {
      if(params.get("period") === periodoTeste) await held
      await route.fulfill({json:dashboardFixture(params)}).catch(() => {})
    }
    const pending = page.waitForRequest(request => new URL(request.url()).searchParams.get("period") === periodoTeste)
    try{
      await page.getByRole("combobox",{name:"Período",exact:true}).selectOption(periodoTeste)
      await pending
      await expect(page.locator(".kpiGrid")).toHaveCount(0)
      await expect(page.locator(".dataTable")).toHaveCount(0)
      await expect(page.locator(".comparisonStrip")).toHaveCount(0)
      await expect(page.locator(".coveragePanel")).toHaveCount(0)
      await expect(page.locator(".leaflet-container")).toHaveCount(0)
      await expect(page.locator("canvas")).toHaveCount(0)
      await expect(page.getByRole("combobox",{name:"Período",exact:true})).toHaveValue(periodoTeste)
      await expect(page.locator(".dashboardResults")).toHaveAttribute("aria-busy","true")
      await expect(page.locator(".dashboardResults").getByRole("status")).toContainText("Carregando")
      release()
      await expect(page.locator(".dashboardResults")).toHaveAttribute("aria-busy","false")
      await expect(page.locator("canvas").first()).toBeVisible()
    }finally{ release() }
  })
}

for(const failure of ["rede","servidor"]){
  test(`falha de ${failure} conserva filtros e permite recuperar sem recarregar`, async ({page,dashboardApi}) => {
    await page.goto("/")
    await expect(page.locator(".kpiValue").first()).toHaveText("12")
    dashboardApi.respond = async (route,params) => {
      if(params.get("period") !== periodoTeste){
        await route.fulfill({json:dashboardFixture(params)})
      }else if(failure === "rede"){
        await route.abort("connectionfailed")
      }else{
        await route.fulfill({status:503,json:{detail:"Servico temporariamente indisponivel"}})
      }
    }
    await page.getByRole("combobox",{name:"Período",exact:true}).selectOption(periodoTeste)
    await expect(page.locator(".errorBox")).toBeVisible()
    await expect(page.getByRole("heading",{name:"Visão Geral",exact:true})).toBeVisible()
    await expect(page.getByRole("combobox",{name:"Período",exact:true})).toHaveValue(periodoTeste)
    await expect(page.getByRole("alert")).toBeVisible()
    await expect(page.locator(".kpiGrid")).toHaveCount(0)
    await expect(page.locator("canvas")).toHaveCount(0)
    await page.getByRole("combobox",{name:"Período",exact:true}).selectOption("all")
    await expect(page.locator(".kpiValue").first()).toHaveText("12")
    await expect(page.getByRole("alert")).toHaveCount(0)
  })
}

test("selecao persistida permanece legivel antes da resposta", async ({page,dashboardApi}) => {
  await page.addInitScript(filters => localStorage.setItem("foco.globalFilters.v03",JSON.stringify(filters)), {
    period:periodoTeste,type:tipoTeste,municipality:municipioTeste,
    unit:unidadeTeste,subtype:subtipoTeste,shift:turnoTeste,
  })
  let release!:() => void
  const held = new Promise<void>(resolve => { release = resolve })
  dashboardApi.respond = async (route,params) => {
    await held
    await route.fulfill({json:dashboardFixture(params)}).catch(() => {})
  }
  try{
    await page.goto("/")
    await expect.poll(() => dashboardApi.requests.length).toBeGreaterThan(0)
    for(const [name,value] of [["Período",periodoTeste],["Tipificação",tipoTeste],
      ["Município",municipioTeste],["Unidade",unidadeTeste],["Subtipo",subtipoTeste],["Turno",turnoTeste]]){
      await expect(page.getByRole("combobox",{name,exact:true})).toHaveValue(value)
    }
    await expect(page.locator(".kpiGrid")).toHaveCount(0)
    release()
    await expect(page.locator(".kpiValue").first()).toHaveText("4")
  }finally{ release() }
})

test("cobertura zero nao e substituida por 24 faixas horarias", async ({page,dashboardApi}) => {
  dashboardApi.respond = async route => {
    const data = dashboardFixture(undefined,0)
    data.overview.coverage = {...data.overview.coverage,types:0,municipalities:0,units:0,hours:0}
    data.types.items = []; data.cities.items = []; data.units.items = []; data.shifts.items = []
    await route.fulfill({json:data})
  }
  await page.goto("/")
  await expect(page.locator(".kpiValue").first()).toHaveText("0")
  await expect(page.locator(".coveragePanel")).toContainText("0 faixas horárias")
  await expect(page.locator(".coveragePanel")).not.toContainText("24 faixas horárias")
})


test("permite repetir carga inicial apos backend indisponivel", async ({page,dashboardApi}) => {
  dashboardApi.respond = async route => { await route.abort("connectionfailed") }
  await page.goto("/")
  await expect(page.getByRole("alert")).toBeVisible()
  await expect(page.locator(".kpiGrid")).toHaveCount(0)
  const requested = dashboardApi.requests.length
  dashboardApi.respond = async (route,params) => { await route.fulfill({json:dashboardFixture(params)}) }
  await page.getByRole("button",{name:"Tentar novamente",exact:true}).click()
  await expect(page.locator(".kpiValue").first()).toHaveText("12")
  await expect.poll(() => dashboardApi.requests.length).toBeGreaterThan(requested)
  await expect(page.getByRole("combobox",{name:"Período",exact:true})).toHaveValue("all")
  await expect(page.getByRole("alert")).toHaveCount(0)
})

test("repetir requisicao preserva filtros e nao exibe resultados antigos", async ({page,dashboardApi}) => {
  await page.goto("/")
  await expect(page.locator(".kpiValue").first()).toHaveText("12")
  await page.getByRole("combobox",{name:"Tipificação",exact:true}).selectOption(tipoTeste)
  await expect(page.locator(".kpiValue").first()).toHaveText("4")
  dashboardApi.respond = async route => { await route.fulfill({status:503,json:{detail:"Indisponivel para teste"}}) }
  await page.getByRole("combobox",{name:"Período",exact:true}).selectOption(periodoTeste)
  await expect(page.getByRole("alert")).toBeVisible()
  const previous = dashboardApi.requests.at(-1)!.search
  const stored = await page.evaluate(() => localStorage.getItem("foco.globalFilters.v03"))
  let release!:() => void
  const held = new Promise<void>(resolve => { release = resolve })
  dashboardApi.respond = async (route,params) => {
    await held
    await route.fulfill({json:dashboardFixture(params)}).catch(() => {})
  }
  const requested = dashboardApi.requests.length
  try{
    await page.getByRole("button",{name:"Tentar novamente",exact:true}).click()
    await expect.poll(() => dashboardApi.requests.length).toBeGreaterThan(requested)
    expect(dashboardApi.requests.at(-1)!.search).toBe(previous)
    await expect(page.locator(".dashboardResults")).toHaveAttribute("aria-busy","true")
    await expect(page.locator(".kpiGrid")).toHaveCount(0)
    await expect(page.getByRole("alert")).toHaveCount(0)
    release()
    await expect(page.locator(".kpiValue").first()).toHaveText("4")
    await expect(page.getByRole("combobox",{name:"Período",exact:true})).toHaveValue(periodoTeste)
    await expect(page.getByRole("combobox",{name:"Tipificação",exact:true})).toHaveValue(tipoTeste)
    expect(await page.evaluate(() => localStorage.getItem("foco.globalFilters.v03"))).toBe(stored)
  }finally{ release() }
})
