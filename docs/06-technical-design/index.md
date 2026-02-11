# Technical Design (TD)

Esta seção detalha a **arquitetura interna e as decisões de implementação** do CarFlow. O documento serve como referência para o desenvolvimento, manutenção e evolução do sistema, cobrindo camadas, fluxos de execução, contratos de interface e requisitos não-funcionais.

O foco deste documento é o escopo **Build (MVP)**:

* **Consulta Pública:** Interface de leitura de preços consolidados (sem login).
* **Processamento Batch:** Rotina mensal de consolidação de dados.
* **Observabilidade:** Registro técnico de logs de consulta para auditoria e análise.

---

## 1. Arquitetura em Camadas

O sistema segue uma arquitetura baseada em camadas (Layered Architecture) para garantir a separação de responsabilidades e facilitar testes.

[![Arquitetura de Camadas](../assets/diagrams/componentes-alto-nivel.png){ width="320" }](../assets/diagrams/componentes-alto-nivel.png){ .glightbox }

### Responsabilidades dos Componentes

* **Presentation Layer (Streamlit UI)**
* Responsável pela renderização de filtros (widgets) e visualização de dados.
* Gerencia o estado da sessão (*Session State*) e cache de interface.
* **Não contém regra de negócio**: apenas valida entradas básicas e invoca o *Service*.
* Trata os retornos do serviço para exibir feedback visual (*Success*, *Warning/No Result*, *Error*).


* **Service Layer (Business Logic)**
* Núcleo da aplicação. Implementa os casos de uso do sistema.
* Orquestra as chamadas ao repositório e aplica regras de negócio (ex: cálculo de variação percentual, formatação de dados para gráficos).
* Garante que todo acesso de consulta gere um registro de log (regra de auditoria).


* **Repository Layer (Data Access)**
* Abstração do banco de dados utilizando **SQLAlchemy**.
* Converte objetos de domínio para queries SQL e vice-versa.
* Isola a aplicação de detalhes específicos do banco (PostgreSQL).


* **Database (PostgreSQL)**
* Armazena os dados transacionais (`price_collections`), analíticos (`monthly_averages`) e logs (`query_logs`).



---

## 2. Fluxo de Dados e Dependências

O diagrama abaixo ilustra como os dados fluem entre o processo de carga (Batch) e o consumo (Consulta).

[![Fluxo de dados (consulta + batch)](../assets/diagrams/dataflow-01-consulta-batch.png){ width="720" }](../assets/diagrams/dataflow-01-consulta-batch.png){ .glightbox }

### Regras de Integridade do Fluxo

1. **Segregação de Leitura/Escrita:** A consulta pública acessa estritamente a tabela consolidada `monthly_averages`, garantindo performance e protegendo os dados brutos.
2. **Fonte do Batch:** O processo de consolidação lê apenas registros com status `APPROVED` na tabela `price_collections`.
3. **Rastreabilidade:** Toda interação de consulta (inclusive falhas) persiste um evento imutável em `query_logs`.


### 2.1. Detalhamento das Classes (Code Design)

O diagrama de classes abaixo ilustra a separação estrita entre **Regra de Negócio** (Service) e **Persistência** (Repository), seguindo o princípio da Inversão de Dependência (DIP).

[![Diagrama UML](../assets/diagrams/uml_classes.png){ width="520" }](../assets/diagrams/uml_classes.png){ .glightbox }

#### StatisticsService (Domain Layer)
Representa o "cérebro" do processamento Batch.
* **Responsabilidade:** Contém a lógica matemática pura. Não sabe que existe um banco de dados, nem que existe uma interface web.
* **Métodos Chave:**
    * `calculate_mean(data: List[float]) -> Decimal`: Recebe uma lista de preços brutos e devolve a média ponderada.
    * `remove_outliers(data)`: Implementa o algoritmo IQR (Intervalo Interquartil) para expurgar preços irreais (ex: R$ 10,00 ou R$ 1.000.000,00 para um Gol).
    * `consolidate_month(ref_date)`: Orquestra o processo: chama o repositório para buscar dados, limpa, calcula e manda salvar.

#### IRepository (Interface / Contract)
Define o **contrato** de acesso aos dados.
* **Responsabilidade:** Garantir que a camada de serviço não dependa de uma implementação específica de banco (PostgreSQL).
* **Por que usar:** Permite criar um `FakeRepository` (em memória) para rodar testes unitários ultra-rápidos sem precisar subir um container Docker de banco de dados.

#### PostgresRepository (Infrastructure Layer)
A implementação real do contrato.
* **Responsabilidade:** Traduzir as chamadas do Service para dialeto SQL usando **SQLAlchemy**.
* **Métodos Chave:**
    * `get_by_filters(...)`: Monta queries dinâmicas baseadas nos filtros da tela.
    * `save_bulk(...)`: Utiliza operações de *batch insert* para salvar milhares de médias de uma vez, garantindo performance.

#### MonthlyAverage (Data Model)
Representa a estrutura de dados da tabela consolidada.
* **Responsabilidade:** Mapeamento Objeto-Relacional (ORM).
* **Atributos:** É uma classe "anêmica" (focada em dados), contendo `brand_id`, `model_id`, `avg_price` e `month_ref`.

---

### 2.2. Decisão de Design: Repository Pattern

Adotamos o padrão **Repository** para isolar a complexidade do SQLAlchemy.

**Sem Repository (Anti-pattern no Service):**
```python
# Ruim: O Service sabe que existe SQL e Sessão
def calcular_media():
    dados = db.execute("SELECT * FROM table") # Acoplado ao SQL
    # ...calcula...
    db.commit()

```

**Com Repository (Nossa Abordagem):**

```python
# Bom: O Service só fala "Python"
def calcular_media(repo: IRepository):
    dados = repo.fetch_all() # Abstração
    # ...calcula...
    repo.save(resultado)

```

Isso garante que, se mudarmos o banco para MongoDB ou CSV no futuro, a lógica de cálculo de média (Service) **não precisa ser alterada**, apenas a implementação do Repositório.


## 3. Detalhamento: Caso de Uso "Consulta Pública"

### Fluxo de Sequência

[![Sequência consulta pública](../assets/diagrams/sequencia-consulta-publica.png){ width="820" }](../assets/diagrams/sequencia-consulta-publica.png){ .glightbox }

### Contrato da Interface (Service Layer)

**Entrada (DTO/Argumentos):**

* `brand_id` (int, obrigatório)
* `model_id` (int, obrigatório)
* `year_model` (int, obrigatório)

**Saída (Response Object):**

* **Cenário SUCCESS:** Objeto contendo `avg_price` (Decimal), `month_ref` (Date) e `samples_count` (Int).
* **Cenário NO_RESULT:** Retorno vazio ou `None` (interpretado pela UI como "Sem dados para este período").
* **Cenário ERROR:** Exceção tratada ou objeto de erro contendo mensagem amigável (sem expor *stacktrace*).

### Comportamento e Tratamento de Erros

* **Resiliência:** Falhas de conexão com o banco são capturadas no Repositório e relançadas como exceções de domínio (`DatabaseConnectionError`), permitindo que a UI exiba uma mensagem de "Serviço Indisponível" em vez de quebrar.
* **Log de Auditoria:** O registro em `query_logs` ocorre em um bloco `finally` ou via *hook* assíncrono para garantir que seja gravado independente do sucesso da busca.

---

## 4. Detalhamento: Caso de Uso "Batch Mensal" (ETL)

### Fluxo de Sequência

[![Sequência batch mensal](../assets/diagrams/sequencia-batch-mensal.png){ width="820" }](../assets/diagrams/sequencia-batch-mensal.png){ .glightbox }

### Estratégia de Processamento (ETL)

O Batch atua como um processo de **ETL (Extract, Transform, Load)** executado sob demanda ou agendamento.

1. **Extract:** Busca coletas em `price_collections` onde `status='APPROVED'` e `month_ref` corresponde ao período alvo.
2. **Transform:**
* Agrupamento por `(brand_id, model_id, year_model)`.
* Cálculo de estatísticas: Média (`avg`), Contagem (`count`).
* *(Futuro)*: Remoção de *outliers* via desvio padrão ou IQR.


3. **Load:** Persistência na tabela `monthly_averages`.

### Idempotência e Consistência

* O script utiliza a estratégia de **UPSERT** (*Insert on Conflict Update*) baseada na chave única composta `(model_id, year_model, month_ref)`.
* Isso permite que o batch seja reexecutado múltiplas vezes para o mesmo mês sem duplicar dados, apenas atualizando os valores consolidados.

---

## 5. Decisões Técnicas e Trade-offs

### 5.1. Denormalização Controlada

Embora o modelo relacional seja normalizado, as tabelas de negócio (`monthly_averages`, `query_logs`) armazenam redundâncias controladas, como `brand_id` junto ao `model_id`.

* **Motivação:** Eliminar a necessidade de *JOINs* complexos nas consultas de leitura crítica (Dashboard Público), otimizando a performance.
* **Garantia:** A integridade é assegurada pelo processo de ingestão (Batch) e pelas Foreign Keys.

### 5.2. Stack Tecnológica

* **Linguagem:** Python 3.10+ (Tipagem estática com Pydantic/Type Hints).
* **ORM:** SQLAlchemy 2.0 (Gerenciamento de sessões e proteção contra SQL Injection).
* **UI:** Streamlit (Desenvolvimento rápido de interfaces de dados).

---

## 6. Estrutura do Projeto (Source Code)

A organização do código fonte reflete a arquitetura em camadas descrita acima:

```text
src/
├── config/             # Variáveis de ambiente e configuração do DB
├── controllers/        # (Opcional) Lógica intermediária da UI
├── models/             # Classes ORM (SQLAlchemy)
│   ├── base.py
│   ├── domain.py       # User, Brand, Model
│   └── operations.py   # PriceCollection, MonthlyAverage
├── repositories/       # Queries e persistência
│   ├── collection_repo.py
│   └── analytics_repo.py
├── services/           # Regras de Negócio
│   ├── calculator_service.py # Lógica do Batch
│   └── search_service.py     # Lógica da Consulta
├── views/              # Interface Streamlit
│   ├── components/     # Widgets reutilizáveis
│   └── pages/
├── jobs/               # Scripts de execução do Batch
└── utils/              # Loggers, Formatadores e Helpers

```

---

## 7. Requisitos Não-Funcionais

### Performance

* **Indexação:** Índices criados nas colunas de filtro (`brand_id`, `model_id`, `year`) nas tabelas de leitura.
* **Cache:** Utilização do `@st.cache_data` do Streamlit para armazenar listas estáticas (Marcas/Modelos), reduzindo chamadas ao banco.

### Segurança

* **Acesso:** Consulta pública restrita a dados agregados; dados brutos (que poderiam identificar lojas ou vendedores) não são expostos na UI pública.
* **Privacidade:** O `query_logs` não armazena PII (Informação Pessoal Identificável) do usuário da consulta, limitando-se a metadados da requisição.