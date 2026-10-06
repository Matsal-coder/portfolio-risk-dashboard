# Portfolio Risk Dashboard — Arquitetura

## 1. Objetivo

O Portfolio Risk Dashboard é um projeto educacional de gestão de riscos multiativo.

Sua arquitetura foi desenhada para evoluir progressivamente em direção a renda fixa, crédito privado, futuros, ações, opções, VaR, Expected Shortfall e stress testing sem acoplar:

- representação da carteira;
- definições contratuais;
- market data;
- modelos de pricing;
- métricas de risco;
- camada de apresentação.

A separação fundamental permanece:

```text
Position ≠ Instrument ≠ Market Data ≠ Pricing ≠ Risk
```

O Bloco 0 construiu a fundação arquitetônica.

O Bloco 1 adicionou uma camada explícita de matemática financeira, convenções e curvas sem quebrar essa separação.

## 2. Fluxo arquitetônico

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
              │
              ▼
       Simple Valuation


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

As estruturas de matemática financeira e curvas são utilizadas pelos objetos de domínio e consumidas pela aplicação e apresentação sem replicação de fórmulas no dashboard.

## 3. Modelo de domínio

### 3.1 Instrument

`Instrument` descreve o que é um contrato financeiro.

Atributos atuais:

```python
Instrument(
    asset_id: str,
    instrument_type: InstrumentType,
)
```

As definições de instrumentos são imutáveis.

O modelo permanece propositalmente mínimo.

Atributos específicos, como:

- maturity;
- coupon;
- indexador;
- strike;
- underlying;
- contract multiplier;

só devem ser adicionados quando sua semântica econômica passar a ser necessária.

### 3.2 InstrumentType

A enumeração atual suporta:

```text
LTN
NTNF
LFT
NTNB
DEB_PRE
DEB_CDI
DEB_IPCA
DI_FUTURE
FX_FUTURE
EQUITY
EQUITY_OPTION
EVENT
```

Nem todos os tipos possuem implementação de pricing ou valuation atualmente.

### 3.3 InstrumentRegistry

`InstrumentRegistry` fornece resolução centralizada:

```python
registry.get(asset_id)
```

Cadastros duplicados são rejeitados em vez de sobrescritos silenciosamente.

O cadastro persistente de instrumentos é carregado atualmente a partir de:

```text
data/instruments/instruments.csv
```

### 3.4 Position

`Position` representa o que a carteira possui ou deve.

Atributos atuais:

```python
Position(
    asset_id: str,
    instrument_type: InstrumentType,
    book: str,
    quantity: float,
    input_price: float | None,
)
```

As posições são imutáveis.

`quantity` representa a quantidade na unidade econômica natural do respectivo instrumento.

Exemplos futuros podem incluir:

```text
equity → número de ações
future → número de contratos
bond → convenção específica do instrumento
option → convenção de contrato/unidade
```

Portanto, a interpretação de `quantity` deve ser combinada com a especificação contratual do instrumento antes que a exposição econômica seja calculada.

### 3.5 Portfolio

`Portfolio` é uma coleção imutável de posições.

Atualmente fornece operações estruturais como:

```text
books
instrument types
positions agrupadas por book
positions agrupadas por instrument type
```

O Portfolio não executa:

- pricing;
- ingestão de market data;
- construção de curvas;
- cálculos de risco.

## 4. Financial foundation

O Bloco 1 introduziu o pacote:

```text
src/portfolio_risk/financial/
```

com as seguintes responsabilidades:

```text
calendars.py
cashflows.py
compounding.py
day_count.py
discounting.py
```

A camada é independente de instrumentos específicos.

## 5. BusinessCalendar

`BusinessCalendar` é um objeto imutável contendo:

```text
holidays
weekend_days
```

A função de contagem de business days usa o intervalo:

```text
(start, end]
```

e suporta intervalos reversos usando sinal negativo.

A arquitetura não assume silenciosamente um calendário brasileiro padrão.

## 6. Day count conventions

As convenções atuais são:

```text
ACT/365
ACT/360
30E/360
BUS/252
```

A API conceitual é:

```python
year_fraction(
    start,
    end,
    convention,
    calendar=None,
)
```

Características:

### ACT/365

```text
actual calendar days / 365
```

### ACT/360

```text
actual calendar days / 360
```

### 30E/360

Implementa explicitamente a variante europeia:

```text
day = min(day, 30)
```

para início e fim.

### BUS/252

```text
business days / 252
```

Exige `BusinessCalendar` explícito.

## 7. Compounding

A engine diferencia:

```text
SIMPLE
COMPOUNDED
CONTINUOUS
```

`CompoundingConvention` é imutável.

Para `COMPOUNDED`, `frequency` é obrigatória.

Para `SIMPLE` e `CONTINUOUS`, frequência não é aceita.

## 8. Discounting

A camada financeira suporta:

```python
discount_factor_from_rate(...)
rate_from_discount_factor(...)
```

### Simple

Conceitualmente:

```text
DF(t) = 1 / (1 + r × t)
```

### Compounded

Para frequência `m`:

```text
DF(t) = (1 + r/m)^(-m×t)
```

### Continuous

```text
DF(t) = exp(-r×t)
```

As funções:

- suportam taxas negativas quando matematicamente válidas;
- rejeitam estados inválidos;
- implementam round trip rate → DF → rate.

## 9. CashFlow

O modelo genérico é:

```python
CashFlow(
    payment_date: date,
    amount: float,
)
```

Ele é imutável e não possui lógica de pricing.

O objeto não diferencia por conta própria:

- principal;
- coupon;
- redemption;
- fee;
- amortização.

A origem econômica do fluxo pertence ao instrumento ou modelo que o gera.

## 10. Yield curves

O Bloco 1 introduziu:

```text
src/portfolio_risk/curves/
```

com:

```text
models.py
interpolation.py
```

### 10.1 CurveNode

Representação:

```python
CurveNode(
    maturity_date: date,
    zero_rate: float,
)
```

Não armazena redundâncias como:

- discount factor;
- tenor;
- forward rate.

Esses valores são derivados.

### 10.2 YieldCurve

Representação conceitual:

```python
YieldCurve(
    as_of,
    nodes,
    day_count,
    compounding,
    calendar,
    interpolation_method,
)
```

A curva é imutável.

Validações:

- mínimo de dois nodes;
- maturity > as_of;
- maturidades únicas;
- nodes ordenados;
- BUS/252 exige calendário.

## 11. Zero-rate nodes como input

No MVP do Bloco 1, os zero-rate nodes são dados de entrada.

Não existe ainda bootstrap a partir de:

- DI futures;
- swaps;
- títulos;
- instrumentos de inflação;
- instrumentos de crédito.

A construção de curva a partir de quotes de mercado é uma etapa futura.

Essa decisão foi tomada para isolar primeiro:

- convenções;
- interpolação;
- discounting;
- forwards;
- shifts;
- integração arquitetônica.

## 12. Interpolação

A estratégia atualmente implementada é:

```text
LOG_LINEAR_DISCOUNT_FACTOR
```

O algoritmo conceitual é:

```text
left zero rate
right zero rate
      │
      ▼
convert to discount factors
      │
      ▼
ln(DF_left)
ln(DF_right)
      │
      ▼
linear interpolation
      │
      ▼
exp(...)
      │
      ▼
interpolated DF
```

A zero rate para a data intermediária pode então ser recuperada a partir do discount factor.

A interpolação não é feita diretamente nas taxas.

## 13. Extrapolação

Não há extrapolação no Bloco 1.

Consultas antes do primeiro node ou depois do último são rejeitadas.

A arquitetura considera extrapolação uma hipótese financeira explícita e, portanto, não deve assumir automaticamente:

- flat zero rate;
- flat forward;
- slope constante;
- outro método.

## 14. Discount factor na curva

A API pública inclui:

```python
curve.discount_factor(target_date)
```

Comportamento:

```text
target < as_of
    → rejeitado

target == as_of
    → DF = 1

target == node
    → DF derivado diretamente do zero rate do node

target entre nodes
    → interpolação log-linear em DF

target fora dos nodes
    → rejeitado
```

## 15. Zero rate na curva

A API:

```python
curve.zero_rate(target_date)
```

Comportamento:

- `target <= as_of` não possui zero rate válido;
- node exato retorna a taxa armazenada;
- datas intermediárias usam DF interpolado;
- não há extrapolação.

## 16. Forward rates

A API:

```python
curve.forward_rate(
    start_date,
    end_date,
)
```

O forward é derivado de discount factors.

Conceitualmente:

```text
DF(start)
DF(end)
    │
    ▼
DF_forward = DF(end) / DF(start)
    │
    ▼
forward rate
```

A convenção de day count e compounding da curva é reutilizada.

Forward rate não é tratada como previsão econômica automática da taxa futura.

## 17. Curve shifts

### 17.1 Parallel shift

API:

```python
curve.parallel_shift_bps(basis_points)
```

Conversão:

```text
1 bp = 0.0001
100 bp = 0.01
```

Todos os zero-rate nodes são deslocados igualmente.

A curva original permanece inalterada.

### 17.2 Key-rate shift

API:

```python
curve.key_rate_shift_bps(
    maturity_date,
    basis_points,
)
```

A maturity date deve corresponder exatamente a um node existente.

Somente o node selecionado é alterado.

O efeito sobre datas intermediárias surge naturalmente da interpolação.

A implementação atual não representa ainda:

- Key Rate DV01;
- shock triangular;
- weighting por bucket;
- distribuição de choque entre tenores.

### 17.3 Imutabilidade e model_copy

Os shifts atuais utilizam cópia do modelo para alterar apenas zero rates.

Essa decisão é segura no estado atual porque:

- topology da curva não muda;
- maturity dates não mudam;
- convenções não mudam;
- calendar não muda.

Se shifts futuros alterarem estrutura ou datas, a curva deverá ser reconstruída e revalidada integralmente.

## 18. Market Data

Market Data representa o estado do mercado, e não características contratuais.

### 18.1 MarketDataPoint

Representação escalar:

```python
MarketDataPoint(
    key: str,
    value: float,
)
```

Utilizada para dados como:

```text
equity prices
FX rates
outros escalares
```

### 18.2 CurveMarketData

Curvas são representadas separadamente:

```python
CurveMarketData(
    key: str,
    curve: YieldCurve,
)
```

Isso evita tratar uma estrutura temporal como um simples `key → float`.

### 18.3 MarketSnapshot

Representação atual:

```python
MarketSnapshot(
    as_of: date,
    points: tuple[MarketDataPoint, ...],
    curves: tuple[CurveMarketData, ...],
)
```

Validações:

- point keys únicos;
- curve keys únicos;
- todas as curvas compartilham o mesmo `as_of` do snapshot.

APIs atuais:

```python
snapshot.get(key)
snapshot.contains(key)

snapshot.get_curve(key)
snapshot.contains_curve(key)
```

Os namespaces de scalar data e curves permanecem semanticamente separados.

## 19. Market Data Providers

### 19.1 SnapshotMarketDataProvider

Carrega:

```text
data/market/market_snapshot.csv
```

Contrato:

```csv
as_of,key,value
```

Retorna um `MarketSnapshot` contendo scalar points.

### 19.2 CurveSnapshotProvider

Carrega:

```text
data/market/curve_snapshot.csv
```

Contrato:

```csv
as_of,curve_key,maturity_date,zero_rate,day_count,compounding,frequency
```

Responsabilidades:

- validar schema;
- validar uma única data-base;
- agrupar rows por `curve_key`;
- validar convenções consistentes dentro de uma curva;
- construir CurveNodes;
- construir YieldCurve;
- retornar CurveMarketData.

### 19.3 Separação dos providers

Os dois providers foram mantidos separados deliberadamente.

Isso evita transformar o snapshot escalar em um CSV polimórfico com colunas opcionais para diferentes tipos de market data.

## 20. Snapshot Mode

Snapshot Mode permanece uma fundação arquitetônica permanente.

Benefícios:

- testes determinísticos;
- desenvolvimento offline;
- experimentos reproduzíveis;
- comparação entre datas;
- futura construção de cenários;
- futura reprecificação sob stress.

Conceitualmente:

```text
external/live providers futuros
              │
              ▼
       normalization layer
              │
              ▼
        MarketSnapshot
              │
              ▼
       Pricing / Risk
```

O sistema não deve depender diretamente de APIs externas nas camadas de pricing ou risco.

## 21. Calendar registry — decisão adiada

O arquivo de curvas atual não serializa um `BusinessCalendar`.

Por esse motivo, a curva fictícia de exemplo utiliza uma convenção que não exige calendário.

Uma evolução futura poderá introduzir:

```text
calendar_key
```

por exemplo:

```text
BR_ANBIMA
BR_B3
```

e um registry explícito:

```python
calendar_registry.get(...)
```

Não foi criada essa abstração no Bloco 1 para evitar antecipar requisitos ainda não necessários.


## 22. Entrada da carteira

O contrato do portfolio CSV permanece:

```csv
asset_id,instrument_type,book,quantity,price
```

`price` é mapeado para:

```python
Position.input_price
```

A distinção permite evolução futura para:

```text
input_price
model_price
```

O loader valida:

- colunas obrigatórias;
- colunas inesperadas;
- domínio por linha;
- cadastro do asset ID;
- consistência de instrument type;
- quantidades long, short e zero;
- preço opcional.

Linhas duplicadas permanecem preservadas.

## 23. Valuation simplificado

O valuation do Bloco 0 permanece deliberadamente restrito.

Não é o futuro Pricing Engine.

Implementação atual:

```text
EQUITY:
simple input value = quantity × input_price
```

Tipos não suportados não são avaliados silenciosamente.

A aplicação reporta:

```text
valued positions
unsupported positions
total positions
coverage ratio
supported total value
supported value by book
```

Isso impede que um valuation parcial seja confundido com NAV completo.

## 24. Camada de aplicação

`load_project_state()` compõe:

```text
instrument master
portfolio
scalar market snapshot
optional curve snapshot
simple valuation
```

em:

```python
ProjectState
```

O parâmetro de curva é opcional:

```python
curve_path: str | Path | None = None
```

Isso preserva compatibilidade com o fluxo construído no Bloco 0.

## 25. Configuração

`Settings` centraliza:

```text
instrument_path
portfolio_path
market_path
curve_path
```

Todos são derivados de:

```text
project_root
```

Variáveis de ambiente utilizam:

```text
PORTFOLIO_RISK_
```

Um `.env` opcional é suportado.

## 26. Dashboard

O dashboard é implementado com Streamlit.

As seções atuais são:

```text
Portfolio
Simple Valuation
Market Data
Curve Explorer
```

### Curve Explorer

A interface apresenta:

- seleção da curva;
- as-of;
- day count;
- compounding;
- tabela de nodes;
- curva interpolada;
- input de parallel shift;
- Base vs Shifted curve.

A apresentação pode gerar datas para amostragem visual, mas não implementa matemática financeira.

Ela chama APIs públicas como:

```python
curve.zero_rate(...)
curve.parallel_shift_bps(...)
```

Não existem no dashboard implementações de:

- discount factor;
- year fraction;
- interpolação;
- forward rates;
- conversão de basis points em taxa.

## 27. Logging

O logging estruturado utiliza `logging` da biblioteca padrão.

O formatter customizado produz JSON por linha com:

```text
timestamp
level
logger
message
```

A fundação pode ser expandida conforme a aplicação evoluir.

## 28. Estratégia de testes

A estrutura permanece:

```text
tests/
├── integration/
└── unit/
```

### Unit tests

Cobrem atualmente:

- application bootstrap;
- config;
- logging;
- financial conventions;
- calendars;
- cash flows;
- compounding;
- day count;
- discounting;
- curves;
- interpolation;
- instruments;
- market data;
- curve provider;
- portfolio;
- valuation.

### Integration tests

Validam fluxos como:

```text
instrument master → registry → portfolio
portfolio + market snapshot
market snapshot + curve snapshot
portfolio → simplified valuation
```

Os testes financeiros verificam relações matemáticas, e não apenas construção de objetos.

## 29. Limites atuais após o Bloco 1

O projeto ainda não implementa:

- bootstrap de curva por instrumentos;
- market data live;
- curvas oficiais B3/ANBIMA/BCB;
- calendar registry;
- extrapolação;
- pricing de bonds;
- accrued interest;
- duration;
- modified duration;
- DV01;
- Key Rate DV01;
- convexidade;
- private credit pricing;
- credit spread;
- spread duration;
- CS01;
- futures valuation;
- hedge ratios;
- options pricing;
- Greeks;
- implied volatility;
- volatility surfaces;
- VaR;
- Expected Shortfall;
- Monte Carlo de portfolio;
- stress testing completo;
- P&L Explain;
- event derivatives.

Essas ausências são deliberadas.

## 30. Próxima direção arquitetônica

A evolução planejada permanece:

```text
Portfolio
   │
   └── Positions
          │
          ▼
    Instrument Registry
          │
          ▼
       Instruments


Market Data Providers
          │
          ▼
      MarketSnapshot
          │
          ├─────────────┐
          ▼             ▼
       Pricing       Exposure
          │             │
          └──────┬──────┘
                 ▼
                Risk
                 │
                 ▼
             Risk Report
                 │
                 ▼
              Dashboard
```

O Bloco 2 deverá utilizar a fundação financeira e a infraestrutura de curvas para iniciar pricing e risco de renda fixa.

O dashboard permanece uma camada de apresentação durante toda essa evolução.
