# Adaptive Offers Lab

Projeto final da Fase 5 do curso MLET: uma plataforma de experimentação adaptativa que escolhe a próxima ação de campanha segundo o contexto observado e aprende com o resultado informado.

O benchmark é o Hillstrom MineThatData E-Mail Analytics Challenge. O experimento original distribuiu clientes aleatoriamente entre campanha masculina, campanha feminina e ausência de campanha. Ele sustenta a avaliação de políticas adaptativas; não representa clientes de uma instituição financeira nem comprova desempenho em produtos bancários. O caso financeiro é a aplicação de negócio proposta pelo Datathon.

## Entrega do Datathon

| Etapa | Evidência |
| --- | --- |
| 0. Organização | `pyproject.toml`, `requirements.txt`, Docker e README |
| 1. Base e EDA | `notebooks/01_eda.ipynb` e fonte Kaggle |
| 2. Preparação | `src/datathon/data.py` e `src/datathon/features.py` |
| 3. Baseline e adaptativo | `notebooks/02_baseline_vs_bandit.ipynb` e `scripts/run_experiment.py` |
| 4. Avaliação e cinco casos | `tests/test_golden_set.py` e notebook |
| 5. Serviço demonstrável | FastAPI, interface em `/` e `/docs` |
| 6. Nuvem | seção “Arquitetura-alvo” |
| 7. MLOps | MLflow local no Compose |
| 8. Apresentação | `video.txt` após a gravação final |

## Dados e limites

Fonte: [Hillstrom no Kaggle](https://www.kaggle.com/datasets/bofulee/kevin-hillstrom-minethatdata-e-mailanalytics/data). Referência original: [MineThatData](https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html). O módulo de dados também baixa a cópia pública pela URL original.

O CSV possui 64.000 registros e as colunas `recency`, `history_segment`, `history`, `mens`, `womens`, `zip_code`, `newbie`, `channel`, `segment`, `visit`, `conversion` e `spend`. `segment` é a ação sorteada e não entra no contexto. Usamos apenas informações disponíveis antes da campanha. Não há identificadores pessoais nem atributos financeiros de produção. Perfis anonimizados podem ter os mesmos valores; essas linhas são mantidas porque podem representar clientes diferentes.

`conversion` é o alvo principal. A política recebe feedback binário no ambiente local. A ação histórica tem propensão próxima de um terço, permitindo replay e IPS. Os conjuntos são separados por ação com semente registrada. O trabalho não inventa conversões para produtos que não existem na base.

## Modelo e avaliação

O baseline principal é a regra fixa conservadora “não enviar campanha” (`no_email`). Também registramos a melhor ação fixa global como referência adicional. O modelo é Thompson Sampling Beta-Bernoulli contextual, com `Beta(1, 1)` por segmento de recência e afinidade de categoria.

No replay, uma linha atualiza a política somente quando a ação escolhida coincide com a ação registrada. O valor é reponderado pela propensão de um terço. A política é ajustada no treino, escolhida na validação e avaliada no teste por IPS. A conclusão mostra linhas casadas e incerteza; nenhuma semente é escolhida depois de observar o teste.

## Execução local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
python scripts/run_experiment.py
python scripts/track_mlflow.py
python scripts/build_policy_snapshot.py
pytest
```

Se `data/raw/hillstrom.csv` não existir, ele será baixado. Dados brutos, bancos, estado da política, artefatos MLflow e resultados intermediários ficam fora do Git.

```powershell
docker compose up --build
```

Abra `http://localhost:8080`, `http://localhost:8080/docs` e `http://localhost:5000`. Para observabilidade local:

```powershell
docker compose --profile monitoring up --build
```

O ambiente local é o modo completo: SQLite persiste decisões e feedback no volume `api_state`, e o estado Bayesiano é salvo em `state/policy.json`. Feedback repetido é idempotente; resultado contraditório é rejeitado.

## API

```powershell
Invoke-RestMethod http://localhost:8080/recommend -Method Post -ContentType 'application/json' -Body '{"recency":3,"history":350,"mens":1,"womens":0,"newbie":0,"zip_code":"Urban","channel":"Web"}'
```

O retorno contém `decision_id`, ação, segmento, versão, médias posteriores e indicação de exploração. Esse identificador é usado em `/feedback`.

## Arquitetura-alvo

Docker Compose executa FastAPI, SQLite, MLflow e, opcionalmente, Prometheus e Grafana. Essa é a implementação demonstrável.

Como arquitetura conceitual em AWS, dados e artefatos poderiam ficar em S3; um job prepararia features; uma tabela online substituiria SQLite; ECR armazenaria a imagem; ECS/Fargate serviria a API; CloudWatch acompanharia latência, erros, exploração e drift. IAM separaria permissões e logs não conteriam dados pessoais. Nenhum recurso AWS é provisionado.

Como publicação complementar, a mesma imagem pode ser enviada ao Artifact Registry e executada no Cloud Run em modo `readonly`, carregando um snapshot congelado. O modo público não grava feedback porque o sistema de arquivos do Cloud Run não é armazenamento persistente. O aprendizado completo permanece no Docker local.

Depois de autenticar o `gcloud`, a publicação opcional usa `scripts/deploy-cloud-run.ps1`. O script constrói a imagem localmente, envia-a ao Artifact Registry e limita o serviço a uma instância. O padrão exige autenticação; `-AllowUnauthenticated` é uma escolha explícita para uma demonstração pública.

## Qualidade e governança

O projeto usa layout `src`, tipagem, validação Pydantic, SQLite transacional, política serializável e testes unitários e de integração. Os notebooks explicam objetivo, método, evidência e limitações. Comentários registram decisões e invariantes; não há caminhos absolutos, credenciais, dados pessoais ou referências ao processo de autoria.

Em um produto real, comunicação e atributos sensíveis passariam por revisão humana, com finalidade, minimização e retenção definidas. Esta entrega é um benchmark educacional, sem decisão automática de crédito.

## Versionamento e apresentação

`.gitignore` separa código e evidências pequenas de dados brutos, estado local, volumes, credenciais e arquivos da gravação. `.dockerignore` evita levar esse material para a imagem. O vídeo terá até cinco minutos e mostrará problema, dados, baseline, política, aplicação local e limitações. Após a gravação, `video.txt` conterá a URL definitiva em um commit próprio.
