# FOCO — Sistema de Identidade Visual e Personalidade

## 1. Status

Este documento é **normativo para o produto FOCO** e complementa o Manual de Identidade Visual do CBMMS.

Em caso de conflito entre este documento e o Manual de Identidade Visual do CBMMS, prevalece o Manual institucional.

## 2. Referência institucional

Fonte primária:

- `Manual-de-Identidade-Visual-CBMMS.pdf`

O FOCO deve respeitar a marca institucional, suas assinaturas, área protetiva, proporções, cores, tipografia e usos proibidos.

## 3. Personalidade do sistema

O FOCO deve transmitir:

- prontidão;
- precisão;
- confiabilidade;
- disciplina;
- sobriedade;
- leitura rápida;
- inteligência operacional;
- clareza na tomada de decisão.

O FOCO **não** deve parecer:

- interface de jogo;
- painel neon;
- produto promocional;
- dashboard decorativo;
- sistema excessivamente colorido;
- interface com animações que distraiam da informação.

## 4. Princípio visual

A identidade institucional e a visualização de dados possuem funções diferentes.

### Identidade institucional
Usa prioritariamente:
- Goles;
- Jalde;
- marca oficial;
- emblema;
- elementos gráficos autorizados.

### Visualização de dados
Pode usar cores funcionais adicionais para:
- séries;
- categorias;
- níveis de SLA;
- alertas;
- polígonos territoriais;
- acessibilidade.

Essas cores funcionais **não alteram a marca** e devem permanecer subordinadas à identidade institucional.

## 5. Cores oficiais

Conforme o padrão cromático da marca:

### Goles
- CMYK: C0 M100 Y100 K10
- RGB: 216, 49, 53
- HEX: `#D83135`
- Pantone: 711 C

### Jalde
- CMYK: C0 M20 Y100 K0
- RGB: 255, 204, 41
- HEX: `#FFCC29`
- Pantone: 123 C

No FOCO:
- Goles é a cor institucional primária.
- Jalde é cor de destaque, atenção e ênfase institucional.
- Não utilizar o vermelho como cor de erro em todos os contextos sem diferenciação semântica.
- Não utilizar Jalde como cor de texto longo sobre fundo claro.

## 6. Neutros de interface

Os neutros abaixo são tokens do FOCO, e não cores heráldicas:

```css
--foco-bg: #101114;
--foco-surface-1: #17191d;
--foco-surface-2: #202329;
--foco-border: #30343b;
--foco-text: #f4f5f6;
--foco-text-muted: #aeb4bd;
```

São usados para garantir boa legibilidade no modo escuro.

## 7. Tipografia

O Manual institucional define:

- TheMix8 ExtraBold;
- TheMix7 Bold;
- Arial;
- Arial Black;
- Infinite Justice como famílias auxiliares em aplicações previstas.

Para o software:

1. utilizar TheMix quando houver licenciamento e disponibilização institucional adequada;
2. não incorporar/distribuir arquivos de fonte sem autorização;
3. usar `Arial, Helvetica, sans-serif` como fallback seguro;
4. utilizar peso e hierarquia tipográfica para reproduzir a personalidade institucional sem falsificar a marca.

Sugestão:

```css
--font-ui: Arial, Helvetica, sans-serif;
--font-heading: Arial Black, Arial, Helvetica, sans-serif;
```

## 8. Marca

A versão horizontal é preferencial quando houver espaço.

A versão vertical é utilizada quando a composição for predominantemente vertical.

Em fundo escuro, utilizar a versão negativa oficial quando necessário.

Obrigatório:
- preservar proporção;
- preservar espaçamento;
- preservar cores;
- respeitar área protetiva;
- utilizar ativos oficiais.

Proibido:
- distorcer;
- redesenhar;
- alterar alinhamento;
- alterar espaçamento entre letras;
- alterar cores;
- recortar partes do emblema;
- aplicar sobre fundo sem contraste;
- utilizar elementos internos do brasão isoladamente.

## 9. Aplicação da marca no FOCO

A marca institucional não precisa aparecer em todos os cards.

Uso recomendado:
- tela de login;
- sidebar/cabeçalho principal;
- relatórios;
- modo sala de situação;
- tela "Sobre";
- documentos exportados.

No cabeçalho do produto pode existir a assinatura:

```text
FOCO
Inteligência Operacional
```

Essa assinatura de produto não substitui a marca institucional.

## 10. Elementos gráficos institucionais

O Manual apresenta:
- faixas amarelas;
- bumerangue;
- flecha formada pela combinação dos elementos.

No FOCO podem ser utilizados de forma discreta em:
- splash/login;
- separadores;
- cabeçalhos de relatório;
- transições;
- fundos institucionais;
- modo sala de situação.

Não usar esses elementos como decoração repetitiva em todos os cards.

## 11. Gráficos e mapas

A paleta dos gráficos deve priorizar contraste e significado.

### Semântica
- Goles: destaque institucional, seleção ativa ou criticidade quando aplicável.
- Jalde: atenção.
- Verde: dentro da meta/sucesso.
- Azul/ciano: informação ou série neutra.
- Cinza: referência, indisponível ou não classificado.

Nunca usar somente cor para diferenciar estados. Complementar com:
- legenda;
- rótulo;
- símbolo;
- padrão de linha;
- texto.

## 12. Microcopy

Tom:
- objetivo;
- técnico;
- curto;
- institucional;
- não alarmista.

Preferir:
- `Integração indisponível`
- `12 registros requerem validação`
- `SLA calculável em 78,4% da base`

Evitar:
- `Ops!`
- `Algo deu errado :(`
- linguagem excessivamente informal;
- mensagens vagas.

## 13. Estados operacionais

Toda tela deve tratar:
- carregando;
- sem dados;
- dado parcial;
- dado DEMO;
- erro;
- conexão indisponível;
- filtro ativo;
- atualização em andamento.

## 14. Desenhos, mockups e protótipos

Qualquer desenho ou protótipo do FOCO deve:
1. partir do sistema de identidade descrito aqui;
2. manter a marca conforme o manual;
3. usar Goles/Jalde como assinatura, não como preenchimento indiscriminado;
4. priorizar leitura em 1920x1080;
5. manter boa leitura em notebook;
6. tratar mapas como ferramenta analítica, não decorativa;
7. evitar estética roxa/neon da referência inicial;
8. preservar a estrutura dark, modular e densa aprovada para o FOCO.

## 15. Checklist visual

Antes de aprovar uma tela:
- [ ] Marca oficial não foi alterada.
- [ ] Área protetiva foi respeitada.
- [ ] Goles/Jalde estão corretos.
- [ ] Contraste é adequado.
- [ ] Filtros ativos estão visíveis.
- [ ] Cores de gráficos possuem significado.
- [ ] Não há excesso de informação decorativa.
- [ ] Estados vazio/erro/loading foram previstos.
- [ ] Dado DEMO está identificado.
- [ ] A tela funciona em 1920x1080.
