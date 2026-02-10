# Escopo (IN/OUT)

Este documento define o **escopo do CarFlow** para esta entrega, separando claramente:
- o que será **implementado (build)**, e
- o que será **apenas documentado (spec-only)**.

> Objetivo: evitar “scope creep” e deixar rastreável o que entrou/saiu da versão.

---

## Visão Geral do Sistema

O **CarFlow** é um sistema de **captura e consulta pública de preços de veículos** (referência tipo FIPE),
com processamento mensal para **consolidação de médias** e disponibilização rápida para consulta.

### Premissas do build
- **Sem login** na consulta pública.
- Banco **PostgreSQL** com acesso via **SQLAlchemy**.
- **Batch mensal** consolidando dados aprovados para leitura rápida.
- **Logs de consulta** sem dados pessoais.

---

## Escopo Implementado (BUILD)

### 1) Consulta pública (Streamlit)
**Objetivo:** permitir ao usuário consultar o preço consolidado.

**Fluxo:**
1. Seleciona **Marca**
2. Seleciona **Modelo**
3. Seleciona **Ano-modelo**
4. O sistema retorna:
   - **preço consolidado**
   - **mês de referência** (`month_ref`)

**Regras (build):**
- Consulta lê **somente** `monthly_averages`.
- Toda consulta registra um evento em `query_logs`:
  - `SUCCESS` quando encontra resultado
  - `NO_RESULT` quando não encontra
  - `ERROR` se ocorrer falha

---

### 2) Batch mensal de consolidação
**Objetivo:** consolidar coletas aprovadas em uma tabela otimizada para leitura.

**Entrada:** `price_collections`  
**Saída:** `monthly_averages`

**Regras (build):**
- Usar **apenas** coletas com `approval_status = APPROVED`.
- Agrupar por:
  - `brand_id`, `model_id`, `year_model`, `month_ref`
- Gerar:
  - `avg_price` (obrigatório)
  - métricas opcionais (se você decidir manter): `median_price`, `std_dev`, `samples_count`

---

### 3) Armazenamento e estrutura mínima de dados
**Tabelas do build:**
- `brands` e `models` (catálogo)
- `stores` (origem/simulação)
- `price_collections` (coletas brutas)
- `monthly_averages` (consolidado para consulta)
- `query_logs` (auditoria técnica)

> Observação: `stores` e `price_collections` podem ser alimentadas por seed/dados simulados nesta versão.

---

## Escopo Documentado (SPEC-ONLY)

Nesta entrega, o processo completo é **documentado**, mas não implementado (build) em UI/CRUD.

### Papéis operacionais (não implementados)
- Coordenador (planejamento/validação)
- Pesquisador (coleta)
- Admin/Gerente/Lojista (cadastros e governança)

### Funcionalidades spec-only
- CRUD de usuários e autenticação
- CRUD completo de lojas/rotas/roteiros
- UI de aprovação (aprovar/rejeitar coletas)
- Gestão regional e atribuição de pesquisadores
- Painéis operacionais (métricas, produtividade, pendências)
- Auditoria avançada (trilhas completas, relatórios)

---

## Fora do Escopo (OUT)

Itens explicitamente fora desta versão:
- Autenticação/autorização (login e perfis)
- Cadastros operacionais completos (usuários, roteiros, permissões)
- Coleta mobile/field app
- Integrações externas (FIPE oficial, ETL completo, mensageria)
- LGPD avançado (base legal, consentimento, minimização formal completa)
- Observabilidade completa (tracing, dashboards, alertas)

---

## Critérios de Pronto (DoD) da entrega

Consideramos esta entrega pronta quando:
- A **consulta pública** funciona de ponta a ponta usando `monthly_averages`.
- O **batch** mensal gera/atualiza `monthly_averages` a partir de `price_collections` **APPROVED**.
- Toda consulta gera um registro em `query_logs` (sem dados pessoais).
- A documentação apresenta:
  - processo (BPMN + fluxos)
  - ERD + dicionário
  - arquitetura e technical design (mínimo)
  - qualidade (testes + CI)

---

## Referências internas da documentação
- Processos: `03-processos-bpmn/`
- Modelagem de dados: `04-modelagem-dados/`
- Arquitetura (C4): `05-arquitetura/`
- Technical Design: `06-technical-design/`
- Qualidade: `07-qualidade/`
