# Architectural Decision Records (ADR)

Este documento registra as decisões de arquitetura significativas, seu contexto e consequências.
Serve como memória técnica do projeto **CarFlow**.

---

## ADR-001: Uso do Streamlit como Monólito Modular

*   **Status:** Aceito
*   **Data:** 2024-02-01
*   **Contexto:**
    Precisávamos de uma interface web rápida para o MVP (Build), sem a complexidade de manter um Frontend (React/Vue) e um Backend (FastAPI/Django) separados neste momento.
*   **Decisão:**
    Utilizar o **Streamlit** como stack única.
*   **Consequências:**
    *   (+) Desenvolvimento extremamente rápido (Python-only).
    *   (+) Deploy simplificado (apenas 1 container Docker).
    *   (-) Acoplamento entre UI e lógica se não houver disciplina (mitigado pela **ADR-002**).
    *   (-) Menor flexibilidade visual comparado a HTML/CSS puro.

---

## ADR-002: Arquitetura em Camadas (Layered Architecture)

*   **Status:** Aceito
*   **Data:** 2024-02-02
*   **Contexto:**
    Frameworks low-code como Streamlit tendem a virar "scripts espaguete" (mistura de SQL, lógica e UI no mesmo arquivo). Precisávamos garantir testabilidade e manutenibilidade.
*   **Decisão:**
    Separar rigorosamente o código em: `View` (Streamlit), `Controller` (Validação), `Service` (Regra de Negócio) e `Repository` (SQL).
*   **Consequências:**
    *   (+) Lógica de cálculo de média testável unitariamente sem abrir o navegador.
    *   (+) Possibilidade de trocar o Streamlit por FastAPI no futuro reaproveitando toda a camada de Service/Repository.
    *   (-) Boilerplate (código repetitivo) maior para criar novas funcionalidades simples.

---

## ADR-003: Repository Pattern com SQLAlchemy

*   **Status:** Aceito
*   **Data:** 2024-02-03
*   **Contexto:**
    Necessidade de isolar a tecnologia de banco de dados e facilitar testes unitários com *mocking*.
*   **Decisão:**
    Implementar o padrão **Repository** para abstrair todas as chamadas `session.query()`, `session.add()`, etc. O *Service* nunca chama o SQLAlchemy diretamente.
*   **Consequências:**
    *   (+) Testes de services não precisam de banco de dados real (usamos `FakeRepository`).
    *   (+) Consultas ficam centralizadas e reutilizáveis.
    *   (-) Curva de aprendizado e verbosidade inicial.

---

## ADR-004: Processamento Batch Síncrono (MVP)

*   **Status:** Aceito (Provisório)
*   **Data:** 2024-02-05
*   **Contexto:**
    O cálculo de médias mensais é pesado, mas no MVP o volume de dados é controlado (milhares de linhas, não milhões). Arquiteturas de filas (RabbitMQ/Kafka) adicionariam complexidade infraestrutural desnecessária agora.
*   **Decisão:**
    Executar o **ETL Batch** como um script Python simples (`src/batch_etl.py`) acionado sob demanda ou cronjob.
*   **Consequências:**
    *   (+) Infraestrutura leve (apenas Postgres e App).
    *   (-) Se o volume explodir, o processo pode sofrer timeout ou travar o banco.
    *   (*) **Mitigação:** Processamento é feito em transações e o script roda separado do processo web.

---

## ADR-005: Denormalização Controlada (`monthly_averages`)

*   **Status:** Aceito
*   **Data:** 2024-02-06
*   **Contexto:**
    A consulta pública precisa ser instantânea. Fazer `JOINs` entre `price_collections`, `brands`, `models` e calcular `AVG()` em tempo real a cada clique seria inviável em escala.
*   **Decisão:**
    Criar uma tabela consolidada (`monthly_averages`) que já contém os dados prontos para leitura, incluindo redundância de IDs (`brand_id`, `model_id`) para evitar JOINs complexos na leitura.
*   **Consequências:**
    *   (+) Leitura ultra-rápida (SELECT simples por índice).
    *   (-) Necessidade de manter consistência (o Batch é responsável por isso).