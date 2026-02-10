# Requisitos

## Objetivo
O CarFlow é um sistema de **captura e consulta de preços de veículos (tipo FIPE)**.  
A solução contempla o **processo completo** (cadastros, roteiros, coleta e aprovação), porém a implementação (build) foca em:
- **Consulta Pública (sem login)**  
- **Batch mensal** de consolidação de médias
- **Registro de log de consultas** (sem dados pessoais)

---

## Atores e papéis
### Papéis do sistema (visão completa)
- **Administrador**: gerencia usuários e perfis
- **Gerente**: gerencia dados globais (marcas/modelos e demais cadastros globais)
- **Coordenador**: define roteiro semanal e aprova coletas/lojas na sua região
- **Pesquisador**: realiza coleta em lojas e pode sugerir novas lojas
- **Lojista**: solicita cadastro da própria loja
- **Usuário Público**: consulta preço médio consolidado (sem login)
- **Sistema (Batch)**: processa coletas aprovadas e consolida médias mensais

---

## Matriz de permissões (resumo)
| Papel | Ações principais | Implementação |
|------|------------------|---------------|
| Administrador | Cadastrar/editar/inativar usuários | Spec-only |
| Gerente | Gerenciar marcas/modelos e dados globais | Spec-only |
| Coordenador | Definir roteiro semanal, aprovar coletas e lojas | Spec-only |
| Pesquisador | Registrar coletas, sugerir lojas | Spec-only |
| Lojista | Solicitar cadastro de loja | Spec-only |
| Usuário Público | Consultar preços consolidados (marca→modelo→ano) | **Build** |
| Sistema (Batch) | Consolidar médias mensais | **Build** |

> Observação: papéis **Spec-only** serão detalhados por fluxos/diagramas e wireframes, mas não serão implementados como telas/CRUD completos.

---

## Regras de negócio (versão 1)
### Consulta pública (US07)
- A consulta deve permitir filtros em cascata: **Marca → Modelo → Ano-modelo**.
- O resultado deve exibir **valor consolidado** e **mês de referência**.
- A consulta **não exige login**.
- O sistema deve armazenar o **log de consulta** para análise posterior, sem dados pessoais.

### Consolidação mensal (US08)
- O batch considera **coletas aprovadas** dentro do período mensal.
- Consolida valores por: **(marca, modelo, ano-modelo, mês de referência)**.
- Gera tabela otimizada para leitura na consulta pública (ex.: `monthly_averages`).
- Tratamento de outliers: definido na seção de Technical Design (inicialmente pode ser simples e documentado).

---

## User Stories (catálogo)
### Spec-only (não implementadas)
- **US01** — Administrador: Gestão de usuários (cadastrar/editar/inativar)
- **US02** — Gerente: Gestão de marcas/modelos e dados globais
- **US03-A** — Lojista: Solicitar cadastro de loja
- **US03-B** — Coordenador: Aprovar solicitações de lojas
- **US04** — Coordenador: Definição de roteiro semanal por região
- **US05** — Pesquisador: Coleta de preços em loja
- **US06** — Coordenador: Validação/aprovação de coletas
- **US09** — Pesquisador: Sugestão de nova loja

### Build (implementadas)
- **US07** — Usuário público: Consulta de preços consolidados (sem login)
- **US08** — Sistema: Batch mensal de cálculo e consolidação de médias

---

## Requisitos não-funcionais (NFR) – mínimo
- **Rastreabilidade**: artefatos (BPMN/ERD/C4/TD) versionados no repositório e referenciados na documentação.
- **Observabilidade**: registrar logs de consulta (sem dados pessoais).
- **Reprodutibilidade**: ambiente local via Docker Compose.
- **Qualidade**: testes automatizados para lógica do batch e pipeline de CI.
