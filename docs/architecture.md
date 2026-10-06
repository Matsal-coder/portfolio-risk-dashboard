# Portfolio Risk Dashboard — Arquitetura

## 1. Objetivo

O Portfolio Risk Dashboard é um projeto educacional de gestão de riscos multiativo.

Sua arquitetura foi desenhada para suportar progressivamente renda fixa, crédito privado, futuros, ações, opções, VaR, Expected Shortfall e stress testing sem acoplar a representação da carteira diretamente a providers de market data, modelos de pricing ou código de apresentação.

A separação fundamental é:

```text
Position ≠ Instrument ≠ Market Data ≠ Pricing ≠ Risk
```

## 2. Fluxo arquitetônico

A arquitetura atual do Bloco 0 é:

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
       MarketSnapshot


Portfolio
MarketSnapshot
Valuation Summary
              │
              ▼
          ProjectState
              │
              ▼
        Streamlit Dashboard
```

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

O modelo é propositalmente mínimo. Atributos contratuais específicos, como vencimento, cupom, indexador, strike, underlying e contract multiplier, só serão introduzidos quando sua semântica financeira for implementada.

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

O Portfolio não executa pricing, ingestão de market data ou cálculos de risco.

## 4. Entrada da carteira

O contrato do portfolio CSV é:

```csv
asset_id,instrument_type,book,quantity,price
```

`price` é mapeado para:

```python
Position.input_price
```

A distinção de nomenclatura é intencional, pois a arquitetura futura deverá separar:

```text
input_price
model_price
```

O loader valida:

- colunas obrigatórias;
- colunas inesperadas;
- validação de domínio por linha;
- asset IDs cadastrados;
- consistência entre o instrument type do CSV e o Instrument Registry;
- quantidades positivas, negativas e zeradas;
- input price opcional.

Linhas duplicadas da carteira são preservadas atualmente em vez de agregadas automaticamente.

## 5. Market Data

Market Data representa o estado do mercado, e não características dos contratos financeiros.

### 5.1 MarketDataPoint

Representação escalar atual:

```python
MarketDataPoint(
    key: str,
    value: float,
)
```

Esse modelo é propositalmente mínimo.

Blocos futuros poderão introduzir estruturas fortemente tipadas para:

- curvas de juros;
- curvas de inflação;
- credit spreads;
- FX;
- superfícies de volatilidade;
- outros fatores de risco.

### 5.2 MarketSnapshot

Um `MarketSnapshot` representa market data normalizado para uma única data de valuation:

```python
MarketSnapshot(
    as_of: date,
    points: tuple[MarketDataPoint, ...],
)
```

As chaves de market data devem ser únicas dentro de um snapshot.

### 5.3 MarketDataProvider

Providers obedecem ao contrato conceitual:

```python
load() -> MarketSnapshot
```

A primeira implementação é:

```text
SnapshotMarketDataProvider
```

que carrega dados locais via CSV.

Isso permite que providers live futuros normalizem dados externos para a mesma representação interna, sem acoplar pricing ou risk a APIs externas.

## 6. Snapshot Mode

A arquitetura inicial prioriza snapshots locais e reproduzíveis.

Benefícios:

- testes determinísticos;
- desenvolvimento offline;
- experimentos educacionais reproduzíveis;
- comparação entre datas de valuation;
- base para futuros cenários e stress tests.

O arquivo de snapshot atualmente possui:

```csv
as_of,key,value
```

e deve conter exatamente uma data-base.

## 7. Valuation simplificado

O Bloco 0 implementa uma camada de valuation deliberadamente restrita.

Ela não deve ser interpretada como o futuro Pricing Engine.

A implementação atual suporta:

```text
EQUITY:
simple input value = quantity × input_price
```

Tipos de instrumento não suportados geram uma condição explícita de valuation não suportado.

No nível do portfolio, o sistema reporta:

```text
valued positions
unsupported positions
total positions
coverage ratio
supported total value
supported value by book
```

Isso evita que um valuation parcial seja apresentado como NAV completo.

### Por que não existe um multiplier universal?

Instrumentos diferentes possuem convenções econômicas diferentes.

Por exemplo, futuros podem exigir tamanho de contrato, convenção de cotação e multiplicadores; opções podem ter premium value, underlying notional e exposições ajustadas por Greeks.

Por isso a arquitetura evita definir:

```python
Instrument.multiplier = 1
```

ou:

```python
Position.market_value = quantity * price
```

como regras universais.

Especificações contratuais e lógica de valuation específicas por instrumento serão introduzidas nos próximos blocos.

## 8. Camada de aplicação

`load_project_state()` compõe o estado atual do sistema:

```text
instrument master
portfolio
market snapshot
simple valuation
```

em um `ProjectState`.

Isso impede que a camada de apresentação replique lógica de infraestrutura ou de domínio.

## 9. Dashboard

O dashboard é implementado com Streamlit.

Página atual:

```text
Portfolio / Market Data
```

Ela apresenta:

- número de posições;
- número de books;
- número de tipos de instrumento;
- tabela da carteira;
- cobertura do valuation simplificado;
- valor simplificado suportado;
- valor suportado por book;
- data-base de market data;
- observações de market data.

Fórmulas financeiras não são implementadas no dashboard.

## 10. Configuração

Os caminhos da aplicação são centralizados por:

```text
portfolio_risk.config.settings.Settings
```

Variáveis de ambiente utilizam o prefixo:

```text
PORTFOLIO_RISK_
```

Um arquivo `.env` opcional é suportado e excluído do Git.

## 11. Logging

O logging estruturado utiliza o pacote padrão `logging` do Python.

O formatter customizado produz registros JSON em uma única linha contendo:

```text
timestamp
level
logger
message
```

Essa fundação pode ser expandida conforme as necessidades operacionais crescerem.

## 12. Estratégia de testes

Os testes são separados em:

```text
tests/
├── unit/
└── integration/
```

Testes unitários validam componentes individuais e comportamento de domínio.

Testes de integração validam fluxos utilizando os arquivos reais do projeto, incluindo:

```text
instrument master → registry → portfolio
portfolio + market snapshot
portfolio → simplified valuation
```

## 13. Limites atuais

O Bloco 0 não implementa:

- curvas de juros;
- pricing de bonds;
- accrued interest;
- duration;
- modified duration;
- DV01;
- Key Rate DV01;
- convexidade;
- credit spreads;
- spread duration;
- CS01;
- convenções de valuation/exposição de futuros;
- pricing de opções;
- Greeks;
- volatilidade implícita;
- VaR;
- Expected Shortfall;
- Monte Carlo;
- stress testing;
- APIs live de market data;
- P&L Explain;
- event derivatives.

Essas ausências são deliberadas.

## 14. Direção arquitetônica futura

A evolução planejada é:

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
          ├────────────┐
          ▼            ▼
       Pricing       Exposure
          │            │
          └──────┬─────┘
                 ▼
              Risk
                 │
                 ▼
           Risk Report
                 │
                 ▼
             Dashboard
```

O dashboard permanece como camada de apresentação ao longo dessa evolução.
