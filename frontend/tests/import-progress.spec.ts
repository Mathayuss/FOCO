import { test, expect } from "./support"

const preview = {
  headers:["Nº/ANO","DATA DO REGISTRO","FATO","MUNICÍPIO"],
  recognized_headers:["id_origem","registro_em","tipo","municipio"],
  missing_required_headers:[],
  total_rows:1,
  valid_rows:1,
  invalid_rows:0,
  issues:[],
  validation_errors:[],
  can_commit:true,
  source_format:"csv",
  source_profile:"RELATORIO_SEJUSP",
  registration_years:[2026],
  registration_periods:["2026-10"],
  valid_rows_without_registration_date:0,
  existing_rows:0,
  new_rows:1,
  column_mappings:[],
  unmapped_headers:[],
  sensitive_rows:0,
  invalid_coordinate_rows:0,
  missing_coordinate_rows:1,
  warnings:[],
  already_imported:false,
  previous_import_batch_id:null,
  previous_import_status:null,
  previous_import_at:null,
}

const commit = {
  id_lote_importacao:15,
  source_format:"csv",
  source_profile:"RELATORIO_SEJUSP",
  source_scope:"RELATORIO_SEJUSP",
  registration_years:[2026],
  registration_periods:["2026-10"],
  valid_rows_without_registration_date:0,
  total_rows:1,
  inserted_rows:1,
  skipped_duplicate_rows:0,
  invalid_rows:0,
  sensitive_rows:0,
  invalid_coordinate_rows:0,
  missing_coordinate_rows:1,
  issues:[],
  validation_errors:[],
  warnings:[],
  can_commit:true,
}

const importFile = {
  name:"ocorrencias-2026.csv",
  mimeType:"text/csv",
  buffer:Buffer.from("Nº/ANO;DATA DO REGISTRO;FATO;MUNICÍPIO\n1/2026;01/10/2026;INCÊNDIO;Campo Grande\n"),
}

async function openImports(page:import("@playwright/test").Page){
  await page.route("**/api/v1/imports/lotes*", route => route.fulfill({json:{items:[],total:0,limite:8,deslocamento:0}}))
  await page.goto("/")
  await expect(page.locator(".kpiValue").first()).toHaveText("12")
  await page.getByRole("button",{name:"Importações",exact:true}).click()
  await expect(page.getByRole("heading",{name:"Importações",exact:true})).toBeVisible()
}

async function selectImportFile(page:import("@playwright/test").Page){
  await page.locator('input[type="file"]').setInputFiles(importFile)
}

test("mostra analise do arquivo enquanto a previa esta pendente", async ({page}) => {
  let release!:() => void
  const held = new Promise<void>(resolve => { release = resolve })
  await page.route("**/api/v1/imports/preview", async route => {
    await held
    await route.fulfill({json:preview}).catch(() => {})
  })
  await openImports(page)

  try{
    await selectImportFile(page)

    const dialog = page.getByRole("dialog")
    await expect(dialog).toBeVisible()
    await expect(dialog.getByRole("heading")).toHaveText(/Enviando arquivo|Analisando arquivo/)
    await expect(dialog).toContainText("ocorrencias-2026.csv")
    await expect(dialog).toContainText("Análise e validação")
    await expect(dialog.getByRole("progressbar")).toBeVisible()
    await expect(page.getByRole("button",{name:"Importar linhas válidas"})).toBeDisabled()
    await expect.poll(()=>page.evaluate(()=>document.body.style.overflow)).toBe("hidden")
    await page.keyboard.press("Escape")
    await expect(dialog).toBeVisible()
    const box=await dialog.boundingBox()
    const viewport=page.viewportSize()
    expect(box).not.toBeNull()
    expect(viewport).not.toBeNull()
    expect(box!.x).toBeGreaterThanOrEqual(0)
    expect(box!.y).toBeGreaterThanOrEqual(0)
    expect(box!.x+box!.width).toBeLessThanOrEqual(viewport!.width)
    expect(box!.y+box!.height).toBeLessThanOrEqual(viewport!.height)

    release()
    await expect(dialog.getByRole("heading")).toHaveText("Arquivo pronto para importar")
    await expect(dialog.getByRole("button",{name:"Importar agora"})).toBeVisible()
    await expect(dialog).toContainText("1 linha nova")
    await expect(page.getByText("Pronto para importar",{exact:true})).toBeVisible()
    await expect(page.locator(".metricRow.good").filter({hasText:"Válidas"})).toContainText("1 · 100%")
    await expect(page.locator(".importSummary")).toContainText("10/2026")
    await page.keyboard.press("Shift+Tab")
    await expect(dialog.getByRole("button",{name:"Importar agora"})).toBeFocused()
    await page.keyboard.press("Tab")
    await expect(dialog.getByRole("button",{name:"Fechar"})).toBeFocused()
    await page.keyboard.press("Escape")
    await expect(dialog).toBeHidden()
    await expect.poll(()=>page.evaluate(()=>document.body.style.overflow)).toBe("")
  }finally{ release() }
})

test("mostra consolidacao durante a confirmacao e fecha apos concluir", async ({page}) => {
  let releaseCommit!:() => void
  const heldCommit = new Promise<void>(resolve => { releaseCommit = resolve })
  await page.route("**/api/v1/imports/preview", route => route.fulfill({json:preview}))
  await page.route("**/api/v1/imports", async route => {
    await heldCommit
    await route.fulfill({json:commit}).catch(() => {})
  })
  await openImports(page)

  try{
    await selectImportFile(page)

    const dialog = page.getByRole("dialog")
    await expect(dialog.getByRole("heading")).toHaveText("Arquivo pronto para importar")
    await dialog.getByRole("button",{name:"Importar agora"}).click()
    await expect(dialog).toBeVisible()
    await expect(dialog.getByRole("heading")).toHaveText(/Enviando arquivo|Importando dados/)
    await expect(dialog).toContainText("Validação e consolidação")
    await expect(dialog).toContainText("Nenhuma linha será exibida no dashboard antes da conclusão")

    releaseCommit()
    await expect(dialog.getByRole("heading")).toHaveText("Importação concluída")
    await expect(dialog).toContainText("1 inserida")
    await expect(dialog.getByRole("button",{name:"Abrir dashboard"})).toBeVisible()
    await expect(page.locator(".importResult").getByText("Importação concluída",{exact:true})).toBeVisible()
    await expect(page.locator(".importResult")).toContainText("Lote #15")
    await expect(page.locator(".importResult")).toContainText("Cobertura por data de registro: 10/2026")
    await dialog.getByRole("button",{name:"Fechar"}).click()
    await expect(dialog).toBeHidden()
  }finally{ releaseCommit() }
})

test("informa duplicidade antes e depois do reprocessamento", async ({page}) => {
  const duplicatePreview = {...preview,new_rows:0,existing_rows:1,already_imported:true,previous_import_batch_id:14,previous_import_status:"concluido"}
  const duplicateCommit = {...commit,inserted_rows:0,skipped_duplicate_rows:1}
  await page.route("**/api/v1/imports/preview", route => route.fulfill({json:duplicatePreview}))
  await page.route("**/api/v1/imports", route => route.fulfill({json:duplicateCommit}))
  await openImports(page)

  await selectImportFile(page)
  const dialog = page.getByRole("dialog")
  await expect(dialog.getByRole("heading")).toHaveText("Dados já importados")
  await expect(dialog).toContainText("1 ocorrência já existe")
  await expect(dialog.getByRole("button",{name:"Registrar reprocessamento"})).toBeVisible()
  await dialog.getByRole("button",{name:"Registrar reprocessamento"}).click()

  await expect(dialog.getByRole("heading")).toHaveText("Nenhum dado novo")
  await expect(dialog).toContainText("1 duplicada")
  await expect(dialog).toContainText("nenhuma ocorrência foi inserida novamente")
})

test("mostra erro da API dentro do modal", async ({page}) => {
  await page.route("**/api/v1/imports/preview", route => route.fulfill({status:400,json:{detail:"Cabeçalhos obrigatórios ausentes: municipio"}}))
  await openImports(page)

  await selectImportFile(page)
  const dialog = page.getByRole("dialog")
  await expect(dialog.getByRole("heading")).toHaveText("Falha na análise")
  await expect(dialog).toContainText("Cabeçalhos obrigatórios ausentes: municipio")
  await expect(dialog.getByRole("button",{name:"Fechar"})).toBeVisible()
})

test("permite selecionar a planilha usando somente o teclado", async ({page}) => {
  await page.route("**/api/v1/imports/preview", route => route.fulfill({json:preview}))
  await openImports(page)

  const selector = page.getByRole("button",{name:"Selecionar arquivo de ocorrências"})
  await selector.focus()
  await expect(selector).toBeFocused()
  const chooserPromise = page.waitForEvent("filechooser")
  await page.keyboard.press("Enter")
  const chooser = await chooserPromise
  await chooser.setFiles(importFile)

  await expect(page.getByRole("dialog").getByRole("heading")).toHaveText("Arquivo pronto para importar")
})
