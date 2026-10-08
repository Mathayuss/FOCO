import type { Locator } from "@playwright/test"
import { test, expect } from "./support"
import { dashboardFixture, periodoTeste, tipoTeste } from "./fixtures/dashboard"

const sparsePeriods = [
  {key:"all",label:"Fev/2025",months:["Fev/2025"]},
  {key:"ano-2025",label:"2025",months:["Fev/2025"]},
  {key:"2025-q1",label:"Fev/2025",months:["Fev/2025"]},
  {key:periodoTeste,label:"Fev/2025",months:["Fev/2025"]},
]

async function clickMonthlyPoint(chart:Locator){
  await expect(chart).toBeVisible()
  let position:{x:number;y:number}|null = null
  await expect.poll(async () => {
    position = await chart.evaluate(element => {
      const canvas = element as HTMLCanvasElement
      const scale = canvas.width / canvas.clientWidth
      const {data,width,height} = canvas.getContext("2d")!.getImageData(0,0,canvas.width,canvas.height)
      let count = 0, xTotal = 0, yTotal = 0
      for(let y=Math.floor(12*scale); y<height-Math.floor(12*scale); y++){
        for(let x=Math.floor(width*.25); x<width*.75; x++){
          const index = (y*width+x)*4
          if(data[index]>200 && data[index+1]>145 && data[index+1]<240 && data[index+2]<110 && data[index+3]>200){
            count++; xTotal+=x; yTotal+=y
          }
        }
      }
      return count ? {x:xTotal/count/scale,y:yTotal/count/scale} : null
    })
    return position !== null
  }).toBe(true)
  await chart.click({position:position!})
}

test("clique mensal em base esparsa seleciona o mes e preserva a tipificacao nos dois paineis", async ({page,dashboardApi}) => {
  dashboardApi.respond = async (route,params) => {
    const data = dashboardFixture(params)
    data.filters.periods = sparsePeriods
    data.overview.available_periods = sparsePeriods
    data.monthly.available_periods = sparsePeriods
    data.monthly.items = [{mes:"Fev/2025",total:data.overview.total,tip:[]}]
    data.monthly.comparison = []
    await route.fulfill({json:data})
  }
  await page.goto("/")
  await expect(page.locator(".kpiValue").first()).toHaveText("12")
  await page.getByRole("combobox",{name:"Tipificação",exact:true}).selectOption(tipoTeste)
  await expect(page.locator(".kpiValue").first()).toHaveText("4")
  const overviewChart = page.locator(".panel").filter({hasText:"Evolução das ocorrências"}).locator("canvas")
  await clickMonthlyPoint(overviewChart)
  await expect(page.getByRole("combobox",{name:"Período",exact:true})).toHaveValue(periodoTeste)
  await expect.poll(() => dashboardApi.requests.at(-1)?.searchParams.get("period")).toBe(periodoTeste)
  await expect(page.getByRole("combobox",{name:"Tipificação",exact:true})).toHaveValue(tipoTeste)
  await page.getByRole("button",{name:"Evolução",exact:true}).click()
  await expect(page.getByRole("heading",{name:"Evolução",exact:true})).toBeVisible()
  await expect(page.getByRole("combobox",{name:"Período",exact:true})).toHaveValue(periodoTeste)
  await expect(page.getByRole("combobox",{name:"Tipificação",exact:true})).toHaveValue(tipoTeste)
  const evolutionChart = page.locator(".panel").filter({hasText:"Evolução mensal"}).locator("canvas")
  await clickMonthlyPoint(evolutionChart)
  await expect(page.getByRole("combobox",{name:"Período",exact:true})).toHaveValue("all")
  await expect(page.getByRole("combobox",{name:"Tipificação",exact:true})).toHaveValue(tipoTeste)
  await expect.poll(() => dashboardApi.requests.at(-1)?.searchParams.get("type")).toBe(tipoTeste)
})
