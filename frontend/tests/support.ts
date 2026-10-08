import { expect, test as base, type Route } from "@playwright/test"
import { dashboardFixture } from "./fixtures/dashboard"

type DashboardApi = {
  requests: URL[]
  respond: (route:Route, params:URLSearchParams) => Promise<void>
}

export const test = base.extend<{dashboardApi:DashboardApi}>({
  dashboardApi: async ({context,baseURL},use) => {
    const unexpected:string[] = []
    const api:DashboardApi = {
      requests: [],
      respond: async (route,params) => { await route.fulfill({json:dashboardFixture(params)}) },
    }
    await context.route("**/*", async route => {
      const request = route.request()
      const url = new URL(request.url())
      const apiPath = url.pathname.startsWith("/api/v1/")
      if(url.origin !== baseURL){
        if(apiPath) unexpected.push(`${request.method()} ${url}`)
        await route.abort("blockedbyclient")
        return
      }
      if(!apiPath){
        await route.continue()
        return
      }
      if(request.method() === "GET" && url.pathname === "/api/v1/health"){
        await route.fulfill({json:{status:"ok",service:"foco-api-testes",database:"ok"}})
      }else if(request.method() === "GET" && url.pathname === "/api/v1/analytics/dashboard"){
        api.requests.push(url)
        await api.respond(route,url.searchParams)
      }else{
        unexpected.push(`${request.method()} ${url}`)
        await route.fulfill({status:503,json:{detail:"Chamada nao permitida pelo teste isolado"}})
      }
    })
    await use(api)
    expect(unexpected,"Nenhuma chamada nao simulada pode acessar a API real").toEqual([])
  },
  page: async ({page,dashboardApi},use) => {
    const errors:string[] = []
    page.on("pageerror",error => errors.push(error.message))
    await use(page)
    expect(dashboardApi.requests.length).toBeGreaterThan(0)
    expect(errors,"Erros JavaScript de pagina").toEqual([])
  },
})

export { expect } from "@playwright/test"
