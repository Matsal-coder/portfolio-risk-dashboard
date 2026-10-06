# Portfolio Risk Dashboard

Sistema educacional de gestão de riscos de uma carteira multiativo, com foco em construção de portfólio, market data, valuation e analytics de risco.

O projeto está sendo desenvolvido de forma incremental com dois objetivos principais:

1. construir um sistema modular de gestão de riscos de portfólio;
2. utilizar o processo de implementação como mecanismo de estudo de conceitos de risco financeiro.

## Estado atual

Os Blocos 0 e 1 estão implementados.

### Bloco 0 — Fundação e Arquitetura

O Bloco 0 estabeleceu:

- domínio de instrumentos;
- Instrument Registry;
- domínio de portfolio e positions;
- carregamento e validação de arquivos CSV;
- Snapshot Mode para market data;
- valuation simplificado e explicitamente restrito;
- ProjectState;
- configuração centralizada;
- logging estruturado;
- dashboard inicial em Streamlit;
- testes unitários e de integração.

### Bloco 1 — Financial Math, Conventions & Curves

O Bloco 1 adicionou:

- calendários de dias úteis;
- day count conventions;
- ACT/365;
- ACT/360;
- 30E/360;
- BUS/252;
- simple compounding;
- compounded compounding;
- continuous compounding;
- conversão entre zero rate e discount factor;
- CashFlow genérico;
- CurveNode;
- YieldCurve;
- interpolação log-linear em discount factors;
- cálculo de discount factors em datas intermediárias;
- cálculo de zero rates interpoladas;
- cálculo de forward rates;
- rejeição explícita de extrapolação;
- parallel shifts em basis points;
- key-rate shifts em nodes;
- integração de yield curves ao MarketSnapshot;
- provider local para snapshots de curvas;
- Curve Explorer no dashboard.

Modelos avançados de pricing e métricas de risco ainda não foram implementados propositalmente.

## Arquitetura

O projeto segue a separação:

```text
Position ≠ Instrument ≠ Market Data ≠ Pricing ≠ Risk
```

Conceitualmente:

```text
data/instruments/instruments.csv
              │
              ▼
      Instrument Loader
              │
              ▼
      Instrument Registry
              │
              │ asset_id
              ▼
data/portfolio/portfolio.csv
              │
              ▼
        Portfolio Loader
              │
              ▼
           Portfolio


data/market/market_snapshot.csv
              │
              ▼
 SnapshotMarketDataProvider
              │
              ▼
        scalar market data
              │
              ├──────────────────┐
              │                  │
              │       data/market/curve_snapshot.csv
              │                  │
              │                  ▼
              │       CurveSnapshotProvider
              │                  │
              └─────────┬────────┘
                        ▼
                 MarketSnapshot
                 ├── points
                 └── curves
                        │
                        ▼
                   ProjectState
                        │
                        ▼
               Streamlit Dashboard
```

A camada de apresentação consome o estado resultante da aplicação e não implementa fórmulas financeiras.

## Estrutura do projeto

```text
portfolio-risk-dashboard/
├── data/
│   ├── instruments/
│   │   └── instruments.csv
│   ├── market/
│   │   ├── curve_snapshot.csv
│   │   └── market_snapshot.csv
│   ├── portfolio/
│   |    └── portfolio.csv
│   └── snapshots/
│
├── dashboard/
│   └── app.py
│
├── docs/
│   └── architecture.md
│
├── notebooks/
│
├── src/
│   └── portfolio_risk/
│       ├── application/
│       ├── config/
│       ├── curves/
│       ├── financial/
│       ├── instruments/
│       ├── market_data/
│       ├── portfolio/
│       └── valuation/
│
├── tests/
│   ├── integration/
│   └── unit/
│
├── pyproject.toml
├── poetry.lock
└── README.md
```

## Requisitos

- Python 3.12+
- Poetry

O projeto atualmente declara suporte para:

```text
>=3.12,<3.14
```

## Instalação

Clone o repositório e instale o ambiente:

```bash
poetry install
```

O ambiente virtual do Poetry está configurado para utilizar uma `.venv` local ao projeto.

## Testes

Executar a suíte completa:

```bash
poetry run pytest
```

Executar somente testes unitários:

```bash
poetry run pytest tests/unit
```

Executar somente testes de integração:

```bash
poetry run pytest tests/integration
```

## Lint e formatação

Verificar lint:

```bash
poetry run ruff check .
```

Verificar formatação:

```bash
poetry run ruff format --check .
```

Aplicar formatação com Ruff:

```bash
poetry run ruff format .
```

## Dashboard

Executar:

```bash
poetry run streamlit run dashboard/app.py
```

O dashboard atual expõe:

### Portfolio

- posições;
- books;
- tipos de instrumento.

### Simple Valuation

- número de posições avaliadas;
- posições não suportadas;
- coverage ratio;
- valor simplificado suportado;
- valor suportado por book.

### Market Data

- data-base do snapshot;
- observações escalares normalizadas.

### Curve Explorer

- seleção da curva;
- data-base;
- day count convention;
- compounding convention;
- nodes da curva;
- curva interpolada;
- parallel shift em basis points;
- comparação visual Base vs Shifted.

Toda a matemática financeira permanece fora do Streamlit.

## Arquivos de entrada

### Cadastro de instrumentos

```text
data/instruments/instruments.csv
```

Schema atual:

```csv
asset_id,instrument_type
```

### Carteira

```text
data/portfolio/portfolio.csv
```

Schema atual:

```csv
asset_id,instrument_type,book,quantity,price
```

O campo `price` é mapeado internamente para `Position.input_price`.

### Snapshot de Market Data

```text
data/market/market_snapshot.csv
```

Schema atual:

```csv
as_of,key,value
```

Um snapshot deve conter uma única data-base (`as_of`).

### Snapshot de curvas

```text
data/market/curve_snapshot.csv
```

Schema atual:

```csv
as_of,curve_key,maturity_date,zero_rate,day_count,compounding,frequency
```

Cada linha representa um node de uma curva.

O provider:

```text
CurveSnapshotProvider
```

agrupa os nodes por `curve_key` e reconstrói objetos `YieldCurve`.

As curvas atualmente utilizadas no arquivo de exemplo são fictícias e determinísticas. O arquivo não representa uma curva oficial de mercado.

## Financial conventions

### Calendário

`BusinessCalendar` representa:

- feriados explícitos;
- dias da semana considerados fim de semana.

A contagem de dias úteis entre duas datas utiliza o intervalo:

```text
(start, end]
```

e suporta intervalos reversos por sinal.

### Day count conventions

As convenções atualmente suportadas são:

```text
ACT/365
ACT/360
30E/360
BUS/252
```

`BUS/252` exige explicitamente um `BusinessCalendar`.

Não existe fallback silencioso para um calendário brasileiro genérico.

### Compounding

As convenções atualmente suportadas são:

```text
SIMPLE
COMPOUNDED
CONTINUOUS
```

No caso `COMPOUNDED`, a frequência é obrigatória.

### Discount factor

A engine suporta conversão:

```text
zero rate → discount factor
discount factor → zero rate
```

As taxas são armazenadas em formato decimal:

```text
0.10 = 10%
```

Taxas negativas são aceitas quando matematicamente válidas para a convenção utilizada.

## Cash flows

O modelo genérico atual é:

```python
CashFlow(
    payment_date: date,
    amount: float,
)
```

`CashFlow` não conhece:

- instrumento;
- principal;
- cupom;
- redemption;
- pricing.

Essas responsabilidades pertencem a camadas específicas de instrumentos e pricing.

## Yield curves

### CurveNode

Representa um node explícito da curva:

```python
CurveNode(
    maturity_date: date,
    zero_rate: float,
)
```

### YieldCurve

Uma curva carrega:

```text
as_of
nodes
day_count
compounding
calendar
interpolation_method
```

A curva é imutável.

Os nodes fornecidos são automaticamente ordenados por maturity date.

São rejeitados:

- menos de dois nodes;
- nodes com vencimento menor ou igual ao `as_of`;
- maturidades duplicadas;
- BUS/252 sem calendário.

## Interpolação

O método atualmente implementado é:

```text
LOG_LINEAR_DISCOUNT_FACTOR
```

O fluxo conceitual é:

```text
zero-rate nodes
      ↓
discount factors
      ↓
interpolação linear em ln(DF)
      ↓
discount factor interpolado
      ↓
zero rate interpolada
```

A escolha evita interpolar diretamente zero rates e mantém discount factors positivos.

## Extrapolação

O Bloco 1 deliberadamente não implementa extrapolação.

Consultas fora do intervalo entre o primeiro e o último node são rejeitadas.

Isso evita introduzir silenciosamente uma hipótese financeira que ainda não foi definida.

## Forward rates

Forward rates são derivados de discount factors.

Conceitualmente:

```text
DF(start)
DF(end)
    ↓
forward discount factor
    ↓
forward rate
```

Forward rate não deve ser interpretada automaticamente como previsão da taxa futura.

## Curve shifts

### Parallel shift

```python
curve.parallel_shift_bps(...)
```

move todos os zero-rate nodes pela mesma quantidade de basis points.

Conversão:

```text
1 bp = 0.0001
100 bp = 0.01 = 1%
```

### Key-rate shift

```python
curve.key_rate_shift_bps(...)
```

altera apenas um node existente identificado pela maturity date.

A versão atual exige correspondência exata com um node da curva.

Não existe ainda:

- distribuição triangular;
- weighting por tenores;
- Key Rate DV01 de instrumentos.

Esses conceitos pertencem aos blocos seguintes.

## Snapshot Mode

O projeto mantém Snapshot Mode como fundação permanente.

Atualmente, `MarketSnapshot` pode carregar:

```text
scalar points
named yield curves
```

Conceitualmente:

```python
MarketSnapshot(
    as_of=...,
    points=(...),
    curves=(...),
)
```

Todas as curvas do snapshot devem compartilhar o mesmo `as_of`.

Isso preserva:

- consistência temporal;
- reprodutibilidade;
- desenvolvimento offline;
- testes determinísticos;
- futura comparação entre cenários.

## Valuation simplificado

O valuation atual continua deliberadamente restrito.

Não existe uma regra universal:

```text
market_value = quantity × price
```

Instrumentos financeiros diferentes possuem convenções distintas de contrato, lote e exposição.

O valuation simplificado atual suporta apenas tipos cuja convenção foi explicitamente implementada.

Ao final do Bloco 1, `EQUITY` continua suportado por:

```text
simple input value = quantity × input_price
```

Instrumentos não suportados são sinalizados explicitamente e não entram silenciosamente nos totais da carteira.

Essa camada não deve ser interpretada como o futuro Pricing Engine.

## Escopo planejado

Os próximos blocos deverão introduzir progressivamente:

- títulos públicos;
- pricing de renda fixa;
- accrued interest;
- duration;
- modified duration;
- DV01;
- Key Rate DV01;
- convexidade;
- crédito privado;
- credit spread;
- spread duration;
- CS01;
- futuros;
- hedge de curva;
- opções;
- Greeks;
- volatilidade;
- VaR;
- Expected Shortfall;
- stress testing;
- full revaluation.

## Limitações conscientes do Bloco 1

O Bloco 1 não implementa:

- bootstrap de curva a partir de instrumentos de mercado;
- curvas oficiais B3, ANBIMA ou BCB;
- APIs live;
- extrapolação;
- calendar registry persistente;
- reconstrução de `BusinessCalendar` via CSV de curva;
- BUS/252 no arquivo atual de curvas;
- pricing de títulos;
- duration;
- DV01;
- Key Rate DV01;
- convexidade;
- credit spread;
- futuros;
- opções;
- VaR;
- Expected Shortfall;
- stress engine completo.

Os zero-rate nodes utilizados atualmente são inputs diretos do MVP.

## Documentação

Consulte:

```text
docs/architecture.md
```

para detalhes sobre as decisões arquitetônicas e limitações atuais.
