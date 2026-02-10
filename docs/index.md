# CarFlow — Documentação

<span class="badge">Projeto individual</span>
<span class="badge">Streamlit</span>
<span class="badge">PostgreSQL</span>
<span class="badge">SQLAlchemy</span>
<span class="badge">Batch mensal</span>

Bem-vindo(a)! Esta documentação concentra os artefatos de engenharia de software do **CarFlow**:
um sistema de captura e consulta de preços de veículos (tipo FIPE), com **consulta pública** e um **batch** mensal
para consolidação dos valores.

<div class="card">
<b>🚀 Por onde começar</b><br>
- Leia o <a href="01-visao-geral/escopo/">Escopo (IN/OUT)</a><br>
- Confira os <b>Requisitos</b> e <b>Regras de negócio</b> (em breve)<br>
- Veja a visão de <b>Arquitetura</b> (em breve)
</div>

<div class="card">
<b>📌 Entregáveis principais</b><br>
- Requisitos + User Stories (todos os papéis)<br>
- BPMN do processo completo (coordenação → coleta → aprovação)<br>
- ERD + dicionário de dados<br>
- Arquitetura (C4) + Technical Design (sequências e componentes)<br>
- Implementação: Consulta pública + Batch<br>
- Testes automatizados + CI
</div>

<div class="card">
<b>🧱 Implementação (build)</b><br>
- Consulta pública (sem login) com filtros em cascata<br>
- Tabela consolidada (médias mensais)<br>
- Log de consultas (<code>query_logs</code>) sem dados pessoais<br>
</div>

<div class="card">
<b>🔗 Links</b><br>
- Repositório: <a href="https://github.com/Tifany-Devil/CarFlow">GitHub</a><br>
- Board: Jira (https://grupob.atlassian.net/jira/software/projects/CAR/boards/102)<br>
</div>
