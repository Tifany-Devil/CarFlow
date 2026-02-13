# Estratégia de Qualidade e Testes

<span class="badge">Pytest</span>
<span class="badge">Ruff</span>
<span class="badge">GitHub Actions</span>
<span class="badge">Coverage</span>

A garantia de qualidade do **CarFlow** baseia-se em uma pirâmide de testes automatizados, análise estática rigorosa e validação contínua via pipeline de CI.

O objetivo é garantir que a lógica crítica (cálculo de médias no Batch) e a integridade dos dados (Repositórios) funcionem conforme o esperado antes de qualquer deploy.

---

## 1. Níveis de Teste

Adotamos a estratégia de testes focado no backend e na lógica de negócio, isolando componentes externos.

### 1.1. Testes Unitários (Service & Batch)
Focam na lógica pura de negócio, sem depender do banco de dados ou interface.
Usamos **Mocks** para simular o comportamento do repositório.

*   **Escopo:** `src/services.py`, `src/batch_etl.py`.
*   **Ferramenta:** `pytest` + `unittest.mock`.
*   **Exemplo:** Verificar se o cálculo da média ponderada ignora valores nulos.

### 1.2. Testes de Integração (Repository & DB)
Validam a comunicação real com o banco de dados (SQLAlchemy) e as constraints do PostgreSQL.
Utilizamos um banco em memória (SQLite) ou container temporário para garantir isolamento.

*   **Escopo:** `src/repositories.py`, `src/models.py`.
*   **Foco:** Garantir que `Foreign Keys`, `Unique Constraints` e `Rollbacks` funcionem.

### 1.3. Testes de Interface (Streamlit Headless)
Utilizamos o framework de testes nativo do Streamlit (`AppTest`) para simular a navegação do usuário sem abrir o navegador (headless).

*   **Cenário:** Simular um usuário filtrando "Toyota" -> "Corolla" -> "2024".
*   **Validação:** Verificar se os KPIs renderizaram e se não houve exceções ("red screen of death").

---

## 2. Análise Estática (Linting)

Para garantir a padronização do código e evitar "code smells", utilizamos o **Ruff** (substituto ultra-rápido para Flake8/Black/Isort).

<div class="card">
<b>🛡️ Regras aplicadas (Ruff)</b><br><br>
<ul>
  <li><b>F401:</b> Imports não utilizados (limpeza de código).</li>
  <li><b>E501:</b> Limite de caracteres por linha (legibilidade).</li>
  <li><b>B*:</b> Bugbear (erros comuns de lógica em Python c/ bugs potenciais).</li>
  <li>Ordenação automática de imports.</li>
</ul>
</div>

---

## 3. Pipeline de CI/CD (GitHub Actions)

A cada `push` ou `pull_request` para a branch `main`, o workflow automatizado é disparado.

[![Pipeline CI](../assets/diagrams/ci-pipeline.png){ width="700" }](../assets/diagrams/ci-pipeline.png){ .glightbox }

### Etapas do Pipeline (`ci.yml`)

1.  **Checkout:** Clona o repositório.
2.  **Setup Python:** Instala Python 3.10.
3.  **Install Dependencies:** Instala libs do `requirements.txt`.
4.  **Linting:** Executa o `ruff check .` para validar estilo.
5.  **Testing:** Executa o `pytest` com cobertura.
    *   *Gate:* Se a cobertura for menor que o limite ou houver falha, o build quebra.

---

## 4. Métricas de Cobertura

Monitoramos a cobertura de código para garantir que caminhos críticos não fiquem desprotegidos.

| Componente | Meta de Cobertura | Crítico? |
| :--- | :--- | :--- |
| **Services (Lógica)** | > 90% | Sim |
| **Repositories (SQL)** | > 80% | Sim |
| **Models (ORM)** | > 95% | Não (declarativo) |
| **UI (Streamlit)** | > 50% | Não (Smoke test) |

> Para rodar localmente e ver o relatório:
> ```bash
> pytest --cov=src tests/
> ```