# FOCO — Áreas Operacionais e Representação Territorial

## 1. Objetivo

Definir como o FOCO deve modelar e exibir as áreas de atuação das unidades operacionais.

Referências:
- `Portaria Nº 348 - regulamentando área atuação CBMMS - BM-1-ANEXO-22224-2.pdf`
- `mapa-operacional-1.pdf`

A norma vigente deve sempre prevalecer sobre representações gráficas históricas.

## 2. Princípio

A área de responsabilidade operacional é um **dado temporal e normativo**.

Ela não deve ser codificada diretamente no frontend.

O banco deve armazenar:
- geometria;
- unidade responsável;
- vigência;
- base normativa;
- tipo de responsabilidade;
- escopo.

## 3. Hierarquia territorial

```text
Território
  ↓
Município
  ↓
Área operacional
  ↓
Região urbana / setor
  ↓
Bairro
  ↓
Ocorrência
```

## 4. Municípios com uma unidade responsável

Quando houver uma única unidade de referência:
- mostrar o município normalmente;
- a camada de área operacional pode permanecer oculta por padrão;
- ao ativar "Área de atuação", exibir contorno da área/unidade.

## 5. Municípios com mais de uma grande unidade

Quando uma cidade possuir mais de uma grande unidade com responsabilidade territorial, o mapa deve dividir visualmente as respectivas áreas.

Padrão:

- contorno sólido para limite da grande unidade;
- preenchimento transparente ou muito discreto;
- rótulo da unidade;
- legenda;
- tooltip com unidade, área e vigência;
- opção de ligar/desligar a camada.

A camada não deve ocultar heatmap, ocorrências ou ruas.

## 6. Campo Grande — referência normativa carregada

A Portaria 348/2021 estabelece, no recorte carregado:

### 1º GBM
Responsabilidade pelas áreas operacionais:
- sul;
- oeste.

Na área urbana:
- Sul = Anhanduizinho + Bandeira.
- Oeste = Imbirussu + Lagoa.

### 6º GBM
Responsabilidade pelas áreas operacionais:
- norte;
- leste.

Na área urbana:
- Norte = Segredo.
- Leste = Centro + Prosa.

### Área rural
A norma também utiliza as rodovias MS-080 e BR-262 como referências para separar as áreas rurais do 1º e 6º GBM.

O FOCO deve armazenar essa regra com vigência e base normativa.

## 7. Subunidades

Quando necessário, permitir segundo nível de contorno:

- grande unidade: linha sólida mais espessa;
- subunidade: linha mais fina ou tracejada.

A visualização deve ser configurável para evitar poluição.

## 8. Representação gráfica

Exemplo:

```text
┌──────────────── MUNICÍPIO ────────────────┐
│                                           │
│   ┌──── Área 6º GBM ──────────────────┐   │
│   │ Norte / Leste                     │   │
│   │       • ocorrências               │   │
│   └───────────────────────────────────┘   │
│                                           │
│   ┌──── Área 1º GBM ──────────────────┐   │
│   │ Sul / Oeste                       │   │
│   │        • ocorrências              │   │
│   └───────────────────────────────────┘   │
└───────────────────────────────────────────┘
```

## 9. Cores territoriais

As cores das áreas são **cores de dados**, não alterações da marca institucional.

Regras:
- não usar duas áreas com cores quase indistinguíveis;
- manter alto contraste entre contornos;
- usar transparência baixa no preenchimento;
- não depender apenas da cor;
- manter legenda persistente;
- permitir padrão de linha quando necessário.

## 10. Camadas do mapa

```text
[ ] Heatmap
[ ] Municípios
[ ] Ocorrências
[ ] Áreas de atuação
[ ] Unidades
[ ] SLA
```

Quando `Áreas de atuação` estiver ativa:
- hover destaca a área;
- clique filtra a unidade;
- painel lateral mostra unidade, municípios/regiões, vigência e base normativa.

## 11. Versionamento

Nunca sobrescrever uma área antiga sem histórico.

Cada área deve possuir:
- `valid_from`;
- `valid_to`;
- documento normativo;
- status.

Assim, uma análise de 2021 pode utilizar a divisão territorial de 2021 e uma análise futura pode utilizar uma divisão posterior.

## 12. Atualização normativa

Sempre que nova portaria/decreto modificar áreas:
1. registrar o documento;
2. encerrar vigência anterior;
3. cadastrar nova versão;
4. validar geometria;
5. executar teste de sobreposição/lacunas;
6. publicar somente após homologação.

## 13. Validação GIS

Antes de publicar polígonos:
- validar geometrias;
- verificar sobreposições não previstas;
- verificar lacunas;
- verificar SRID;
- verificar cobertura municipal;
- comparar com documento oficial.

## 14. Fonte gráfica

`mapa-operacional-1.pdf` deve ser tratado como referência visual para organização territorial estadual.

Não transformar imagem raster em verdade normativa sem confirmação documental.

A geometria definitiva deve vir de:
- shapefile/GeoJSON institucional;
- limites oficiais;
- digitalização homologada;
- fonte geoespacial validada.
