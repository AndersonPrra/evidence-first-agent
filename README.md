# Evidence First Agent

Sistema agentivo para análise de dados de biodiversidade com arquitetura **Evidence First**, desenvolvido para responder perguntas analíticas em linguagem natural utilizando evidências calculadas de forma determinística, auditável e reproduzível.

---

## Sobre o projeto

O **Evidence First Agent** permite que um utilizador faça perguntas sobre dados de monitorização de biodiversidade em linguagem natural.

Em vez de delegar os cálculos ao modelo de linguagem, o sistema separa claramente:

* **interpretação da pergunta**, realizada pelo LLM;
* **execução das análises**, realizada por ferramentas determinísticas;
* **produção das evidências**, realizada pelo Evidence Engine;
* **verificação independente**, realizada pelo Evidence Auditor;
* **comunicação dos resultados**, realizada novamente pelo LLM.

Dessa forma, o modelo de linguagem **não é tratado como fonte de verdade dos dados**.

A arquitetura foi projetada para que os resultados analíticos possam ser rastreados até os dados, parâmetros, execução e métodos utilizados.

---

## Principais características

* Arquitetura **Evidence First**
* Agente baseado em LLM local
* Integração com **Ollama**
* Ferramentas analíticas determinísticas
* Validação independente dos resultados
* Evidências estruturadas e auditáveis
* Rastreabilidade das execuções
* Geração automática de relatórios
* Camadas de dados **Bronze, Silver e Gold**
* Diagnóstico e validação da qualidade dos dados
* Guardrails para evitar interpretações indevidas
* Execução reproduzível
* Interface via linha de comando (CLI)

---

## Arquitetura

O fluxo principal do sistema é:

<img width="700" height="875" alt="Arquitetura Geral" src="https://github.com/user-attachments/assets/62dc101e-651a-4ce5-afcf-ec22c8f4cd76" />

### Princípio central

O LLM interpreta a intenção do utilizador, mas **não calcula diretamente os resultados analíticos**.

Por exemplo, diante da pergunta:

> "Qual mês apresentou a maior riqueza observada de espécies de aves?"

o agente identifica a análise necessária e encaminha a execução para a ferramenta correspondente.

A ferramenta calcula o resultado a partir dos dados e produz uma evidência estruturada. O resultado é então auditado antes de ser apresentado ao utilizador.

---

## Análises disponíveis

### Peak Richness

Identifica o período com maior riqueza observada de espécies.

Método principal:

```python
get_peak_richness_by_month()
```

Exemplo de pergunta:

```text
Qual mês apresentou a maior riqueza observada de espécies de aves?
```

---

### Abundance Summary

Produz um resumo da abundância observada nas unidades amostrais disponíveis.

Método principal:

```python
get_abundance_summary()
```

Exemplo de pergunta:

```text
Qual espécie apresentou a maior abundância observada?
```

---

### Effort Discrepancy

Analisa diferenças relacionadas ao esforço amostral e identifica situações em que comparações diretas podem ser inadequadas.

Método principal:

```python
get_effort_discrepancy_report()
```

Exemplo de pergunta:

```text
Os esforços de amostragem são comparáveis ​​entre os eventos analisados?
```

---

## Evidence First

O sistema utiliza o conceito de **Evidence Claim** para representar os resultados das análises.

Uma evidência contém informações como:

* análise executada;
* resultado;
* fonte dos dados;
* parâmetros utilizados;
* timestamp;
* identificação da execução;
* identificação da análise;
* informações de auditoria.

Conceitualmente, as evidências podem assumir estados como:

```text
VERIFIED
SUPPORTED
UNCERTAIN
UNSUPPORTED
```

### Claim ID × Execution ID

O sistema diferencia:

**`claim_id`**

Identifica uma análise e os seus parâmetros.

**`execution_id`**

Identifica uma execução concreta daquela análise.

Essa separação permite distinguir a definição de uma análise da execução específica que produziu determinado resultado.

---

## Qualidade e guardrails

O sistema possui regras explícitas para evitar interpretações indevidas dos dados.

Entre elas:

* `NULL` não significa automaticamente zero;
* presença de uma espécie não significa ausência fora do registo;
* unidades diferentes de esforço não são automaticamente equivalentes;
* protocolos de amostragem diferentes não são automaticamente comparáveis;
* correlação não deve ser apresentada como causalidade;
* não são realizadas extrapolações ou previsões sem suporte nos dados;
* resultados não são apresentados como conclusões ecológicas além do que as evidências permitem.

Essas regras fazem parte do domínio analítico e são consideradas durante a geração das evidências.

---

## Pipeline de dados

O projeto utiliza a arquitetura **Medallion**:

<img width="800" height="377" alt="Arquitetura dos dados" src="https://github.com/user-attachments/assets/6697f085-0075-44ca-a208-4d014c1eb4d3" />

### Bronze — dados brutos

Contém os dados originais utilizados pelo sistema:
Já foram adicionados à pasta data/bronze_raw os dados brutos do dataset “Bird census counts at the Zwin Nature Park” para testar o sistema, baixados do GBIF, portanto você não precisa se preocupar em baixar/descompactar e subir os dados para a pasta, pois já estão lá.

```text
data/bronze_raw/
├── event.txt
├── occurrence.txt
└── humboldtecologicalinventory.txt
```

---

### Silver — dados processados

Contém os dados preparados para análise:

```text
data/silver_processed/
├── eventos.csv
├── ocorrencias.csv
├── inventarios.csv
├── perfil_dados.json
└── relatorio_qualidade.json
```

Essa camada concentra processos de preparação, padronização e diagnóstico dos dados.

---

### Gold — dados analíticos

Contém tabelas utilizadas diretamente pelas análises:

```text
data/gold_analytical/
├── richness_event.csv
├── richness_month.csv
├── abundance_event.csv
├── composition_event.csv
└── effort_event.csv
```

---

## Tecnologias

O projeto foi desenvolvido utilizando principalmente:

* **Python**
* **Pandas**
* **Pydantic**
* **Ollama**
* **LLM local**
* **JSON / JSONL**
* **CSV**
* **Arquitetura modular**
* **CLI**

O LLM pode ser executado localmente através do Ollama, evitando a necessidade de utilização de uma API externa para a etapa de interpretação e comunicação.

---

## Instalação

### 1. Clonar o repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd evidence-first-agent
```

### 2. Criar ambiente virtual caso queira

```bash
python -m venv .venv
```

No Windows:

```bash
.venv\Scripts\activate
```

No Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Instalar o projeto

```bash
python -m pip install -e .
```

### 4. Instalar o Ollama (IMPORTANTE)

O Ollama pode ser instalado através do site oficial:

https://ollama.com/

No Windows, também é possível utilizar:

```powershell
winget install Ollama.Ollama
```

### 5. Instalar a biblioteca Python do Ollama

```bash
python -m pip install ollama
```

### 6. Instalar o modelo utilizado pelo projeto

Após instalar o Ollama, baixe o modelo configurado no projeto utilizando o comando correspondente ao modelo definido na implementação.

Exemplo:

```bash
ollama pull llama3.2
```

As instruções completas de instalação e configuração estão disponíveis em:

[Instruções Gerais.pdf](https://github.com/user-attachments/files/32381459/Instrucoes.Gerais.pdf)


---

## Execução

Após a instalação, o sistema pode ser executado através de:

```bash
python -m evidence_agent
```

Também é possível executar uma pergunta diretamente:

```bash
python -m evidence_agent --question "What month had the highest observed bird species richness?"
```

Para executar o fluxo de demonstração:

```bash
python -m evidence_agent --demo
```

---

## Estrutura do projeto

<img width="600" height="1067" alt="Estrutura de Pastas e Arquivos" src="https://github.com/user-attachments/assets/6f6a094e-49ec-4bfe-9ee3-3e2ec42bfa00" />

---

## Principais módulos

| Módulo                 | Responsabilidade                              |
| ---------------------- | --------------------------------------------- |
| `bootstrap.py`         | Inicialização e preparação do ambiente        |
| `cli.py`               | Interface de linha de comando                 |
| `llm_service.py`       | Comunicação com o LLM local                   |
| `orchestrator.py`      | Coordenação do fluxo de execução              |
| `skills.py`            | Registro e seleção das capacidades analíticas |
| `report_generator.py`  | Geração de relatórios                         |
| `trace.py`             | Rastreamento das execuções                    |
| `ingestion.py`         | Ingestão e preparação dos dados               |
| `data_profile.py`      | Perfilamento dos dados                        |
| `run_diagnosis.py`     | Diagnóstico da qualidade dos dados            |
| `analytical_tables.py` | Construção das tabelas analíticas             |
| `evidence_engine.py`   | Produção das evidências                       |
| `evidence_auditor.py`  | Verificação independente das evidências       |

---

## Rastreabilidade

As execuções do sistema são registradas em:

```text
logs/execution_trace.jsonl
```

Os relatórios produzidos ficam disponíveis em:

```text
reports/
```

Isso permite acompanhar não apenas o resultado final, mas também informações relacionadas à execução da análise.

---

## Documentação

A documentação detalhada do projeto está disponível no seguinte documento:

[Documentação.pdf](https://github.com/user-attachments/files/32381497/Documentacao.pdf)

---

## Objetivo técnico

O projeto procura demonstrar uma abordagem em que **IA generativa e análise de dados determinística trabalham em conjunto**, mantendo separadas as responsabilidades de:

```text
LLM
↓
Interpretação

Ferramentas analíticas
↓
Cálculo

Evidence Engine
↓
Evidência

Evidence Auditor
↓
Verificação

Report Generator
↓
Comunicação
```

O objetivo é tornar o uso de agentes de IA em análise de dados mais **rastreável, verificável e reproduzível**.

---

## Autor

**José Anderson Pereira**

Cientista e Analista de Dados | Cientista da Computação/Biomédico | Pesquisador em Bioinformática

---
