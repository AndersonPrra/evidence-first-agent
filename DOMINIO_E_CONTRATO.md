# Domínio e Contrato

## 1. Visão Geral do Domínio

### Domínio

**Monitoramento da biodiversidade e ecologia quantitativa**, com foco inicial em **comunidades de aves**.

### Objetivo

Análise de padrões de riqueza, abundância e composição de comunidades de aves a partir de dados de amostragem padronizada no espaço e no tempo.

O sistema deve produzir análises **reprodutíveis, verificáveis e rastreáveis**, reconhecendo quando os dados não são suficientes para responder à pergunta.

### Dados de referência

O conjunto utilizado no desenvolvimento é proveniente do **Zwin Nature Park (Bélgica)**, disponibilizado pelo GBIF, utilizando dados estruturados segundo **Darwin Core** e **Humboldt Core**.

O conjunto possui três componentes principais:

```text
`humboldtecologicalinventory.txt` (Entidade: Protocolo Humboldt - Inventário ecológico)
        ↓
`event.txt` (Entidade: Evento de Amostragem)
        ↓
`occurrence.txt` (Entidade: Ocorrência de espécie/Observação)
```

O sistema é projetado para ser reutilizável dentro de uma família definida de dados de monitoramento da biodiversidade, utilizando um contrato de domínio que permite reconhecer entradas compatíveis, adaptar o fluxo analítico e recusar análises quando os requisitos não forem atendidos.

---

## 2. Estrutura dos Dados

### 2.1 Inventário ecológico

O inventário contém informações sobre o contexto da amostragem, incluindo:

* escopo taxonômico;
* completude do inventário;
* registro de não detecções;
* presença de táxons não alvo;
* protocolo;
* esforço de amostragem;
* disponibilidade de abundância.

Exemplos de campos:

`targetTaxonomicScope`, `taxonCompletenessReported`, `isAbsenceReported`, `protocolNames`, `isAbundanceReported`, `samplingEffortValue`, `samplingEffortUnit`.

O inventário é considerado parte dos **dados analíticos**, e não apenas metadado.

### 2.2 Eventos

Cada evento representa uma unidade de amostragem e pode conter:

* data e horário;
* protocolo;
* esforço/tamanho da amostra;
* localização;
* coordenadas.

Exemplos:

`eventID`, `eventDate`, `samplingProtocol`, `sampleSizeValue`, `sampleSizeUnit`, `locationID`, `decimalLatitude`, `decimalLongitude`.

### 2.3 Ocorrências

As ocorrências representam os registros taxonômicos associados aos eventos.

Exemplos:

`occurrenceID`, `eventID`, `occurrenceStatus`, `individualCount`, `scientificName`, `scientificNameID`, `taxonRank`.

### 2.4 Granularidade

A unidade fundamental das análises é:

> **espécie × evento de amostragem**

Os dados originais não devem ser agregados prematuramente.

Quando necessário, agregações como riqueza por local ou abundância por período devem ocorrer apenas na etapa analítica correspondente.

---

## 3. Requisitos Mínimos de Entrada

O sistema deve verificar se os dados possuem estrutura suficiente para a pergunta solicitada.

### Obrigatórios, conforme a análise

* eventos de amostragem identificáveis;
* relação entre ocorrências e eventos;
* identificação taxonômica utilizável para análises por espécie;
* data para análises temporais;
* localização para análises espaciais;
* informação de esforço quando a comparação depender dela.

O sistema deve interromper ou limitar uma análise quando faltar informação essencial.

A limitação deve ser registrada e explicada no resultado.

---

## 4. Integridade e Qualidade dos Dados

Antes da análise, o sistema deve verificar:

* quantidade e estrutura dos registros;
* valores ausentes;
* duplicidades;
* chaves e relacionamentos entre arquivos;
* inconsistências taxonômicas;
* coordenadas inválidas;
* cobertura temporal;
* protocolos utilizados;
* medidas de esforço;
* registros de presença e não detecção.

As relações entre tabelas devem ser **validadas**, e não assumidas.

Por exemplo:

```text
Humboldt.id → Event.eventID
Occurrence.eventID → Event.eventID
```

O sistema também deve verificar a unicidade de `eventID` e `occurrenceID` antes de tratá-los como identificadores únicos.

---

## 5. Guardrails Analíticos

### 5.1 Presença e não detecção

`occurrenceStatus = absent` significa:

> **não detecção registrada no evento de amostragem**

Não deve ser interpretado automaticamente como ausência absoluta da espécie no local.

### 5.2 Abundância

Quando `occurrenceStatus = present` e `individualCount` estiver preenchido, o valor pode ser utilizado como abundância registrada.

Quando `individualCount` estiver ausente, o registro pode representar apenas presença qualitativa.

Casos como:

```text
absent + individualCount > 0
```

devem ser sinalizados como inconsistência e investigados antes de qualquer correção.

### 5.3 Esforço de amostragem

Diferentes campos de esforço não devem ser considerados equivalentes automaticamente.

Por exemplo:

```text
sampleSizeValue = 120 minute
```

e:

```text
samplingEffortValue = 1.2 personHour
```

podem representar conceitos diferentes.

O sistema deve avaliar a semântica, unidade e comparabilidade antes de realizar conversões ou padronizações.

Quando necessário, a abundância pode ser padronizada por unidade de esforço, desde que a medida seja metodologicamente apropriada.

### 5.4 Protocolos

Diferenças entre protocolos, como:

```text
Point count
Transect count
```

devem ser detectadas e consideradas na análise.

O sistema pode:

* analisar os protocolos separadamente;
* considerar o protocolo na análise;
* restringir a comparação;
* ou interromper a análise quando não houver comparabilidade suficiente.

Não deve assumir automaticamente que os protocolos são equivalentes ou incompatíveis.

### 5.5 Taxonomia

O sistema deve verificar:

* nomes científicos;
* identificadores taxonômicos;
* nível taxonômico;
* status de identificação;
* inconsistências entre registros.

A ausência de `scientificNameID` não implica automaticamente exclusão quando `scientificName` estiver disponível.

### 5.6 Espaço e tempo

Análises espaciais devem validar as coordenadas e sua incerteza.

Análises temporais devem verificar a cobertura temporal antes de inferir tendências.

O sistema não deve produzir uma tendência temporal quando os dados não possuem cobertura suficiente para sustentá-la.

---

## 6. Pipeline de Dados

O processamento segue a arquitetura medalhão com três camadas:

```text
(Bronze) BRUTO → (Prata) PROCESSADO → (Ouro) ANALÍTICO
```

### Dados bruto (Camada Bronze)

Arquivos originais preservados sem alteração.

```text
dados/brutos/
```

### Processado (Camada Prata)

Dados com:

* tipos corrigidos;
* padronizações documentadas;
* validações;
* campos derivados;
* problemas de qualidade identificados.

Exemplo:

```text
dados/processados/
├── eventos.csv
├── ocorrencias.csv
└── inventarios.csv
```

### Analítico (Camada Ouro)

Tabelas específicas para cada análise, preservando a granularidade original quando possível.

Exemplos:

```text
dados/processados/analitico/
├── especie_evento.csv
├── riqueza_evento.csv
└── abundancia_evento.csv
```

Toda transformação deve registrar:

* campo original;
* transformação realizada;
* motivo;
* resultado;
* validação.

---

## 7. Perguntas Analíticas Suportadas

O sistema deve ser capaz de avaliar perguntas como:

1. **Como os dados estão estruturados e quais problemas de qualidade podem afetar a análise da comunidade de aves?**

2. **Como a riqueza e a abundância das comunidades variam entre locais e períodos de amostragem?**

3. **Quais espécies ou grupos de espécies mais contribuem para diferenças na composição das comunidades?**

4. **As diferenças observadas podem estar relacionadas a diferenças no esforço de amostragem?**

5. **Quais padrões relevantes para o monitoramento da biodiversidade são sustentados pelas evidências disponíveis?**

O sistema não precisa executar todas as etapas em todas as perguntas. O fluxo deve ser adaptado ao objetivo da análise.

---

## 8. Fora do Escopo

O sistema não deve produzir automaticamente:

* inferências causais a partir de simples correlações;
* estimativas populacionais sem desenho amostral adequado;
* generalizações para populações, regiões ou períodos não representados;
* tendências temporais sem cobertura suficiente;
* conclusões taxonômicas fora do escopo dos dados;
* imputações automáticas sem justificativa e validação;
* correções automáticas de coordenadas sem evidência;
* equivalência entre diferentes medidas de esforço sem validação;
* comparações entre protocolos sem avaliar sua comparabilidade.

Quando uma pergunta estiver fora do escopo, o sistema deve explicar o motivo e, quando possível, indicar qual análise ainda pode ser realizada.

---

## 9. Hierarquia das Evidências

As afirmações produzidas pelo sistema devem respeitar quatro níveis:

### Observação

Descrição direta dos dados.

> "O evento X registrou 24 espécies."

### Associação

Relação estatística observada.

> "A riqueza apresentou associação com o esforço de amostragem."

### Inferência

Interpretação sustentada pelos dados e pelas premissas do método.

### Causalidade

Relação de causa e efeito.

Não deve ser inferida apenas a partir de uma associação observacional.

---

## 10. Auditoria de Evidências

Toda conclusão apresentada no relatório deve estar vinculada a evidências verificáveis.

Estrutura:

```text
AFIRMAÇÃO
    ↓
EVIDÊNCIA
    ↓
MÉTODO
    ↓
VALIDAÇÃO
    ↓
LIMITAÇÕES
```

Cada evidência deve informar, quando aplicável:

* qual ferramenta foi utilizada;
* quais parâmetros foram utilizados;
* qual resultado foi obtido;
* como o resultado foi validado.

### Estados

* **VERIFIED** — resultado diretamente verificável por operação determinística validada.
* **SUPPORTED** — resultado sustentado, mas dependente de premissas ou escolhas metodológicas.
* **UNCERTAIN** — evidência insuficiente ou conflitante.
* **UNSUPPORTED** — evidência insuficiente para sustentar a afirmação.

Afirmações `UNCERTAIN` ou `UNSUPPORTED` não devem ser apresentadas como conclusões definitivas.

---

## 11. Reprodutibilidade e Rastreabilidade

Cada execução deve gerar registros suficientes para reproduzir e auditar o processo.

Exemplo:

```text
execucoes/<id>/
├── manifesto_entrada.json
├── perfil_dados.json
├── relatorio_qualidade.json
├── contrato_analise.json
├── plano_analise.json
├── decisoes.json
├── evidencias.json
├── validacao.json
└── relatorio.md
```

Devem ser registrados:

* dados utilizados;
* decisões;
* transformações;
* ferramentas executadas;
* resultados;
* validações;
* limitações;
* conclusões.

---

## 12. Princípio Central

O sistema deve seguir uma regra simples:

> **Nenhuma conclusão sem evidência verificável.**

O modelo de linguagem é responsável principalmente por:

* compreender a pergunta;
* planejar a análise;
* selecionar ferramentas;
* interpretar resultados;
* comunicar conclusões e limitações.

Operações críticas, cálculos e validações devem ser realizados por ferramentas determinísticas sempre que possível.

O sistema deve preferir:

> **reconhecer que os dados não permitem uma conclusão a produzir uma conclusão sem suporte.**