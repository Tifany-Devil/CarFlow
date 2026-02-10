# Jira & Planning

Esta seção documenta como o projeto **CarFlow** foi planejado e organizado no **Jira**, incluindo:
- estrutura de épicos (macro-entregas),
- padrão de issues (histórias e tarefas),
- uso de labels (build vs spec-only),
- workflow (A fazer → Em progresso → Feito),
- definição de pronto (DoD) e rastreabilidade com a documentação.

---

## Visão geral do projeto no Jira

O planejamento foi estruturado para um projeto **individual**, com foco em:
- manter **escopo controlado** (build),
- documentar o que é **apenas especificação** (spec-only),
- permitir evolução incremental com entregas pequenas e claras.

[![Quadro do Jira](../assets/jira.png){ width="720" }](../assets/jira.png){ .glightbox }

<div class="card">
<b>📌 Jira (Planning)</b><br><br>
<ul>
  <li>Acompanhe o board, épicos, labels e progresso do projeto.</li>
</ul>
<a class="md-button" href="https://grupob.atlassian.net/jira/software/projects/CAR/boards/102?atlOrigin=eyJpIjoiYTM0NTRkZTYwMjhmNGM5OTkyMDI2OGFiZDJkYmRmNTkiLCJwIjoiaiJ9" target="_blank" rel="noopener">
Abrir Jira
</a>
</div>

---

## Estrutura de Épicos

Os épicos representam “pacotes” de entrega:

- **Engenharia de Requisitos & Design**
- **Arquitetura & Modelagem de Dados**
- **Infraestrutura & Backend (Core)**
- **Frontend & Experiência do Usuário**
- **Qualidade & Entrega**

---

## Tipos de Issues (padrão)

### História (User Story)
Usada para requisitos de valor (ex.: consulta pública, batch mensal).  
Campos mínimos recomendados:
- Como [ator], eu quero [ação], para [valor]
- Critérios de aceite
- Labels: `build` **ou** `spec-only`

### Tarefa
Usada para atividades técnicas/documentais (ex.: diagrama, ERD, pipeline, testes).  
Exemplo de tarefa: testes da lógica de média no batch. :contentReference[oaicite:1]{index=1}

---

## Labels (padrão do projeto)

Para deixar o projeto “auditável” e claro:

- `build` → **será implementado**
- `spec-only` → **apenas documentação / wireframe / diagrama**
- `docs` → item ligado ao MkDocs
- `diagram` → item que gera artefato visual (BPMN/ERD/C4/Sequência)
- `batch` → consolidação mensal
- `db` → modelagem/migração/SQLAlchemy/Postgres
- `ui` → Streamlit

> No export do Jira aparecem labels como `diagram, docs, spec-only`. :contentReference[oaicite:2]{index=2}

---

## Workflow (Kanban)

Colunas sugeridas (simples e eficiente para projeto individual):
1. **A fazer**
2. **Em progresso**
3. **Feito**

Regras práticas:
- Só pode ter **1–2 cards** em “Em progresso” ao mesmo tempo (WIP).
- Tarefas grandes devem ser quebradas (ex.: “Arquitetura C4” vira Contexto / Containers / Componentes).

---

## Definition of Done (DoD)

Uma issue só vai para **Feito** quando:

### Para `docs` / `diagram`
- Arquivo `.md` criado/atualizado no MkDocs
- Imagem exportada em `docs/assets/diagrams/`
- Link no texto do MkDocs apontando para a imagem (com glightbox, quando aplicável)

### Para `build`
- Código implementado
- Teste mínimo (unitário ou validação executável)
- Rodou local via `docker compose up` (quando for infra/backend)
- Documentação “Como rodar” atualizada

---





