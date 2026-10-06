# Portfolio Risk Dashboard

Sistema educacional de gestão de riscos de uma carteira multiativo, com foco em construção de portfólio, market data, valuation e analytics de risco.

O projeto está sendo desenvolvido de forma incremental com dois objetivos principais:

1. construir um sistema modular de gestão de riscos de portfólio;
2. utilizar o processo de implementação como mecanismo de estudo de conceitos de risco financeiro.

## Estado atual

O Bloco 0 — Fundação e Arquitetura está implementado.

Atualmente, o projeto suporta:

- definição de instrumentos e Instrument Registry;
- carregamento do cadastro de instrumentos via CSV;
- carregamento e validação de carteira via CSV;
- posições long, short e zeradas;
- snapshots locais e normalizados de market data;
- valuation simplificado para instrumentos explicitamente suportados;
- acompanhamento da cobertura do valuation;
- apresentação de carteira e market data via Streamlit;
- configuração centralizada;
- logging estruturado em JSON;
- testes unitários e de integração.

Modelos avançados de pricing e métricas de risco ainda não foram implementados propositalmente.

## Arquitetura

O projeto segue a separação:

```text
Position ≠ Instrument ≠ Market Data ≠ Pricing ≠ Risk
```

Conceitualmente:

```text
portfolio.csv
      │
      ▼
Portfolio Loader
      │
      ▼
Portfolio / Positions
      │
      │ asset_id
      ▼
Instrument Registry
      ▲
      │
instruments.csv

market_snapshot.csv
      │
      ▼
Market Data Provider
      │
      ▼
MarketSnapshot
```

A camada de apresentação consome o estado resultante da aplicação e não implementa fórmulas financeiras.

## Estrutura do projeto

```text
portfolio-risk-dashboard/
├── data/
│   ├── instruments/
│   ├── market/
│   ├── portfolio/
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

O dashboard atual expõe a visão Portfolio / Market Data, incluindo:

- posições;
- books;
- tipos de instrumento;
- cobertura do valuation simplificado;
- valor simplificado suportado;
- valor suportado por book;
- data-base do snapshot de market data;
- observações normalizadas de mercado.

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

## Valuation simplificado

O Bloco 0 deliberadamente não implementa uma regra universal:

```text
market_value = quantity × price
```

Instrumentos financeiros diferentes possuem convenções distintas de contrato, lote e exposição.

O valuation simplificado atual suporta apenas tipos de instrumento cuja convenção foi explicitamente definida.

Ao final do Bloco 0, `EQUITY` é suportado por:

```text
simple input value = quantity × input_price
```

Instrumentos não suportados são sinalizados explicitamente e não entram silenciosamente nos totais da carteira.

Essa camada não deve ser interpretada como o futuro Pricing Engine.

## Escopo planejado

Os próximos blocos deverão introduzir progressivamente:

- precificação de títulos públicos e crédito privado;
- curvas;
- duration e modified duration;
- DV01 e Key Rate DV01;
- convexidade;
- credit spread, spread duration e CS01;
- futuros;
- risco de ações e FX;
- opções e Greeks;
- volatilidade;
- VaR e Expected Shortfall;
- stress testing com full revaluation.

## Documentação

Consulte:

```text
docs/architecture.md
```

para detalhes sobre as decisões arquitetônicas e limitações atuais.
