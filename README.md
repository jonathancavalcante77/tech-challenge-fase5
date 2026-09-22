# Adaptive Offers Lab

Projeto final da Fase 5 do curso MLET. A solução implementa uma plataforma local de experimentação adaptativa que escolhe a próxima ação de campanha segundo o contexto disponível, registra a decisão e aprende com feedback binário.

O benchmark é o Hillstrom MineThatData E-Mail Analytics Challenge. O experimento original distribuiu clientes aleatoriamente entre campanha masculina, campanha feminina e ausência de campanha. Ele permite avaliar políticas adaptativas, mas não representa clientes de uma instituição financeira nem comprova desempenho em produtos bancários. O domínio financeiro é a aplicação de negócio proposta pelo Datathon.

## Evidências da entrega

| Etapa | Evidência local |
| --- | --- |
| 0. Organização | `pyproject.toml`, `requirements.txt`, Docker e este README |
| 1. Base e EDA | `notebooks/01_eda.ipynb`, executado e com outputs salvos |
| 2. Preparação | `src/datathon/data.py` e `src/datathon/features.py` |
| 3. Baseline e adaptativo | `notebooks/02_baseline_vs_bandit.ipynb` e `scripts/run_experiment.py` |
| 4. Avaliação e Golden Set | `artifacts/experiment_summary.json` e `artifacts/golden_set.json` |
| 5. Serviço | FastAPI, interface em `/`, contrato em `/docs` e feedback persistente |
| 6. Nuvem | arquitetura conceitual abaixo e script opcional de Cloud Run |
| 7. MLOps | MLflow, Prometheus e Grafana no Docker Compose |
| 8. Apresentação | etapa externa deliberadamente adiada até a revisão final |

O repositório público e o vídeo serão produzidos somente depois da última revisão local.

## Dados e qualidade

Fonte: [Hillstrom no Kaggle](https://www.kaggle.com/datasets/bofulee/kevin-hillstrom-minethatdata-e-mailanalytics/data), versão 1, com licença Apache 2.0 conforme listada pelo uploader. Referência original: [MineThatData](https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html). Fonte, checksum, target, ações e limitações estão versionados em `data/source.json`.

O CSV possui 64.000 registros e as colunas `recency`, `history_segment`, `history`, `mens`, `womens`, `zip_code`, `newbie`, `channel`, `segment`, `visit`, `conversion` e `spend`. O pipeline baixa por arquivo temporário, valida o SHA-256 antes de aceitar o arquivo e rejeita schema, ação ou domínio inválidos.

`segment` é a ação sorteada e não entra no contexto. `conversion` é o alvo principal. A política recebe feedback binário. A atribuição histórica é próxima de um terço por ação, permitindo replay e IPS. Os conjuntos são separados por ação em treino, validação e teste com semente `2026`. Apenas dados anteriores à campanha são disponibilizados à política.

![Distribuição experimental e conversão observada](artifacts/figures/eda_actions.png)

## Política e avaliação

O baseline obrigatório é a regra fixa conservadora `no_email`. A melhor ação fixa global é registrada como referência adicional. A política adaptativa é Thompson Sampling Beta-Bernoulli com prior `Beta(1, 1)` por segmento de recência (`recent`, `middle`, `old`) e afinidade histórica de categoria (`mens`, `womens`, `mixed`, `none`). Histórico, canal, região e condição de cliente novo são validados e registrados, mas a versão atual não os utiliza na chave do posterior.

A política é inicializada no treino, selecionada na validação e avaliada uma única vez no teste. No replay sequencial, ela só aprende quando a ação recomendada coincide com a ação registrada. Cada contribuição é corrigida pela propensão uniforme de um terço. A API chama o mesmo método estocástico `recommend` usado nessa avaliação.

| Política no teste | Valor IPS | IC 95% aproximado | Diferença contra `no_email` |
| --- | ---: | ---: | ---: |
| Baseline `no_email` | 0,007030 | [0,004517; 0,009543] | 0 |
| Melhor ação fixa `mens_email` | 0,014763 | [0,011127; 0,018400] | +0,007733 |
| Thompson Sampling | 0,013826 | [0,010306; 0,017346] | +0,006796 |

Thompson Sampling foi selecionado na validação (`0,008673` contra `0,005860` do baseline) e superou `no_email` no teste. A melhor ação fixa ficou `0,000937` acima do replay adaptativo. Os intervalos se sobrepõem; portanto, o projeto não afirma superioridade estatística do bandit sobre a melhor ação fixa. A taxa de exploração observada foi `18,47%`, com 4.242 linhas casadas no teste.

![Comparação das políticas](artifacts/figures/policy_comparison.png)

![Replay sequencial](artifacts/figures/sequential_replay.png)

## Golden Set

Os cinco casos usam segmentos presentes no snapshot treinado e são executados pelo mesmo Thompson Sampling da API. Com a semente registrada, todos resultaram em aproveitamento da ação com maior média posterior. O resultado detalhado, incluindo contexto, médias, ação de aproveitamento e justificativa, está em `artifacts/golden_set.json` e no notebook de avaliação.

| Caso | Segmento | Recomendação | Faz sentido? | Justificativa resumida |
| --- | --- | --- | --- | --- |
| `recent_mens_web` | `recent:mens` | `mens_email` | Sim | Maior média posterior do segmento |
| `recent_womens_multichannel` | `recent:womens` | `mens_email` | Sim, com ressalva | Diferença posterior mínima para `womens_email`; a incerteza deve ser exposta |
| `middle_mixed_web` | `middle:mixed` | `mens_email` | Sim | Maior média posterior, com evidência segmentada limitada |
| `old_mens_phone` | `old:mens` | `mens_email` | Sim | Maior média posterior do segmento |
| `old_womens_web` | `old:womens` | `mens_email` | Sim, com ressalva | O rótulo descreve categoria de campanha, não gênero do cliente |

Essas decisões fazem sentido dentro do benchmark randomizado. Elas não autorizam decisão de crédito nem personalização com atributos sensíveis.

## Execução local

Requer Python 3.11 ou 3.12.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
python scripts/build_policy_snapshot.py
python scripts/run_experiment.py
python scripts/build_golden_set.py
python scripts/execute_notebooks.py
python scripts/track_mlflow.py
ruff check src app scripts tests
ruff format --check src app scripts tests
pytest --cov=src --cov=app
```

Se `data/raw/hillstrom.csv` não existir, ele será baixado e validado. Dados brutos, bancos, estados mutáveis e volumes permanecem fora do Git. Resumo, Golden Set, figuras e outputs dos notebooks são evidências pequenas e versionáveis.

## API e persistência

O serviço oferece:

- `POST /recommend`: valida o contexto e retorna ação, segmento, versão, médias posteriores, amostras, exploração e identificador da decisão;
- `POST /feedback`: registra recompensa `0` ou `1` e atualiza a política em modo local;
- `GET /health`: saúde e ambiente;
- `GET /metadata`: versão, modo, regra de decisão e estado operacional;
- `GET /metrics`: métricas Prometheus;
- `/docs`: contrato OpenAPI;
- `/`: interface web para demonstração.

Exemplo:

```powershell
$body = @{
  recency = 3
  history = 350
  mens = 1
  womens = 0
  newbie = 0
  zip_code = "Urban"
  channel = "Web"
} | ConvertTo-Json

Invoke-RestMethod http://localhost:8080/recommend `
  -Method Post -ContentType "application/json" -Body $body
```

Uma instalação nova carrega `config/policy_snapshot.json`; ela nunca inicia silenciosamente com priors vazios. Em modo `mutable`, SQLite guarda decisões, feedback e o estado Bayesiano na mesma transação. `state/policy.json` é um espelho escrito de forma atômica. Na reinicialização, o SQLite prevalece, evitando perda de aprendizado se o espelho estiver ausente. Feedback repetido é idempotente e feedback contraditório é rejeitado.

`POLICY_MODE` aceita somente `mutable` e `readonly`. O modo somente leitura usa o snapshot treinado, não registra decisões e rejeita feedback.

## Docker, MLflow e observabilidade

Com o Docker Desktop ativo:

```powershell
docker compose up --build
```

As portas podem ser substituídas por `API_PORT`, `MLFLOW_PORT`, `PROMETHEUS_PORT` e `GRAFANA_PORT`. Isso permite manter outros projetos locais em execução; por exemplo, `$env:API_PORT=8081` publica a API em `8081` sem alterar a porta interna do container.

Acesse:

- aplicação: `http://localhost:8080`;
- OpenAPI: `http://localhost:8080/docs`;
- MLflow: `http://localhost:5000`.

O serviço `tracker` registra automaticamente `artifacts/experiment_summary.json` no servidor MLflow do Compose. Uma chave formada por checksum, semente e política evita runs duplicados.

Para subir também as melhorias opcionais:

```powershell
docker compose --profile monitoring up --build
```

Prometheus fica em `http://localhost:9090` e Grafana em `http://localhost:3000`. No primeiro acesso local ao Grafana, use `admin` como usuário e senha e defina a nova senha solicitada. O dashboard `Adaptive Offers` é provisionado automaticamente e mostra taxa de requisições, p95 de latência, recomendações por ação e exploração. A API também expõe contadores de feedback e quantidade de segmentos da política.

## Arquitetura de nuvem

Em uma arquitetura AWS, dados e artefatos poderiam ficar em S3; um job prepararia as features; DynamoDB ou Aurora substituiria o SQLite; ECR armazenaria a imagem; ECS/Fargate serviria a API; e CloudWatch acompanharia latência, erros, exploração e drift. IAM separaria permissões e os logs não conteriam dados pessoais. Nenhum recurso AWS é necessário para executar esta entrega.

Como extensão pronta para uso futuro, `scripts/deploy-cloud-run.ps1` constrói a mesma imagem, envia ao Artifact Registry e publica no Cloud Run em modo `readonly`. O serviço usa o snapshot treinado incluído na imagem, grava apenas banco temporário em `/tmp`, limita a uma instância e não depende do filesystem efêmero para aprendizado. A implantação real foi deliberadamente adiada até a revisão local final.

## Governança, privacidade e limitações

Esta entrega usa um benchmark público sem identificadores pessoais. Em uma aplicação financeira hipotética que tratasse dados pessoais para personalização de comunicação, a base legal considerada seria o legítimo interesse previsto nos arts. 7º, IX, e 10 da [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm), condicionado a avaliação documentada de balanceamento, expectativa do titular, necessidade, transparência e possibilidade de oposição. Se essa avaliação não sustentasse o tratamento, outra base legal válida, como consentimento específico, precisaria ser definida antes do uso.

A finalidade seria exclusivamente selecionar comunicação comercial. Seriam coletados somente atributos necessários, com retenção limitada, controle de acesso, auditoria e eliminação ao fim da finalidade. A recomendação não produz aprovação, recusa, preço ou limite de crédito. Mudanças de política, campanhas sensíveis e impactos relevantes exigiriam revisão humana. O titular teria canal para informação, contestação e exercício dos direitos aplicáveis.

Limitações principais:

- benchmark de varejo de 2008, sem dados bancários;
- ausência de contrafactuais individuais;
- IPS depende da propensão histórica conhecida;
- intervalos apresentados são aproximações descritivas;
- segmentação deliberadamente simples;
- recomendação estocástica pode variar conforme o estado do gerador;
- desempenho offline não garante resultado em produção.

## Qualidade

O projeto usa layout `src`, validação Pydantic, estado versionado, checksum, SQLite em WAL, escrita atômica, usuário não privilegiado no container e testes unitários e de integração. A suíte cobre API, políticas, replay, persistência, concorrência, recuperação, checksum, configuração e Golden Set.

Antes da publicação final ainda serão feitos uma revisão independente, o clone limpo, a criação do repositório público, a gravação do pitch e a inclusão do link real em `video.txt`.
