# CarFlow — Documentação Técnica

<span class="badge">Projeto individual</span>
<span class="badge">Streamlit</span>
<span class="badge">PostgreSQL</span>
<span class="badge">SQLAlchemy</span>
<span class="badge">Batch mensal</span>

O **CarFlow** é um sistema de **captura e consulta pública de preços de veículos** (referência tipo FIPE),
com processamento mensal para **consolidação de médias** e disponibilização rápida para consulta.

<div class="card">
<b>✅ Escopo do que será implementado (build)</b><br><br>
<ul>
  <li><b>Consulta pública (sem login)</b> com filtros em cascata: Marca → Modelo → Ano-modelo</li>
  <li><b>Batch mensal</b> para consolidar médias em tabela otimizada para leitura</li>
  <li><b>Log de consultas</b> (<code>query_logs</code>) sem dados pessoais, para análise posterior</li>
</ul>
</div>

<div class="card">
<b>📦 Entregáveis de engenharia</b><br><br>
<ul>
  <li>Catálogo de requisitos: atores, permissões, user stories e regras de negócio</li>
  <li>BPMN do processo completo (cadastros → roteiro → coleta → aprovação)</li>
  <li>Modelagem de dados (ERD + dicionário)</li>
  <li>Arquitetura (C4) e Technical Design (componentes + sequências)</li>
  <li>Testes automatizados e pipeline de CI</li>
</ul>
</div>

<div class="card">
<b>🚀 Próximos passos</b><br><br>
<ol>
  <li>Documentar <a href="05-arquitetura/">Arquitetura (C4)</a> (Contexto + Containers + Componentes)</li>
  <li>Documentar <a href="06-technical-design/">Technical Design</a> (camadas, sequências e decisões)</li>
  <li>Fechar <a href="07-qualidade/">Qualidade</a> (estratégia de testes + CI)</li>
</ol>
</div>
