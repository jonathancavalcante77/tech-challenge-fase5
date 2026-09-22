# Plano vigente — Datathon MLET Fase 5

Este documento registra a direção técnica da entrega. O contrato obrigatório está no `POSTECH - MLET - DATATHON.pdf`; as demais aulas justificam práticas, mas não transformam todas as ferramentas apresentadas em requisitos.

## Decisão executiva

O projeto será desenvolvido e executado principalmente no computador, com Docker Compose. A solução utiliza FastAPI, uma interface web própria, SQLite, MLflow local e testes. Streamlit não será utilizado porque a aplicação precisa juntar API, recomendação, feedback, estado da política e modo público em um único serviço controlado.

Cloud Run e Artifact Registry ficam como publicação complementar. O enunciado não exige deploy real; exige uma descrição de arquitetura em nuvem. Não serão usados Firestore, Cloud SQL, Cloud Storage, Secret Manager, Cloud Build, GKE ou Kubernetes. Esses serviços não são necessários ao pipeline local e não são etapas obrigatórias do PDF.

O ambiente local é completo e persistente. A publicação no Cloud Run usa snapshot congelado e modo somente leitura, pois o filesystem de uma instância não deve ser tratado como banco persistente. Não haverá duas implementações diferentes: o mesmo serviço recebe configuração de modo.

## Contrato da banca

| Etapa | Evidência planejada |
| --- | --- |
| 0 | Repositório público, `README.md`, `pyproject.toml` e `requirements.txt` |
| 1 | Link Kaggle, `notebooks/01_eda.ipynb`, limpeza e qualidade |
| 2 | Transformação de contexto e alvo de conversão |
| 3 | Regra fixa `no_email` e Thompson Sampling contextual |
| 4 | Métricas, incerteza e cinco casos do Golden Set |
| 5 | FastAPI e interface web demonstrável |
| 6 | Parágrafos de arquitetura AWS e publicação complementar em Cloud Run |
| 7 | MLflow local com parâmetros, métricas e artefato do experimento |
| 8 | Vídeo de até cinco minutos mostrando a aplicação funcionando |

Toda a explicação necessária para a banca ficará no README, conforme orientação do PDF. O plano não cria documentos de governança soltos para substituir esse arquivo.

## Dados e problema

A base principal é [Kevin Hillstrom MineThatData E-Mail Analytics no Kaggle](https://www.kaggle.com/datasets/bofulee/kevin-hillstrom-minethatdata-e-mailanalytics/data), com referência original em [MineThatData](https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html). Ela contém um experimento público com três ações: campanha masculina, campanha feminina e ausência de campanha.

A plataforma será apresentada no domínio financeiro descrito no desafio, mas o resultado numérico será explicitamente atribuído ao benchmark de campanhas de varejo. Não serão inventadas conversões de crédito ou cartão. Não serão usados identificadores pessoais, patrimônio, renda de produção, gênero de pessoa ou regras privadas.

`segment` identifica a ação que foi sorteada e não é uma feature. O contexto utiliza recência, histórico, afinidade de compras anteriores, cliente novo, região e canal. `conversion` é o alvo principal; `visit` e `spend` servem como análises secundárias. O arquivo bruto fica local, com fonte, versão, checksum e limitações documentados.

## Modelo e avaliação

O baseline principal é a regra fixa conservadora “não enviar campanha”. A melhor ação fixa global também será mostrada como referência adicional. Thompson Sampling Beta-Bernoulli contextual usa prior `Beta(1, 1)` por segmento de recência e afinidade. O estado é serializável e a versão acompanha cada recomendação.

Os dados são divididos por ação em treino, validação e teste com semente registrada. A política é inicializada com o treino, selecionada pela validação e avaliada no teste. No replay, somente a ação observada atualiza a política. O valor é estimado com IPS usando propensão de um terço; são reportados linhas casadas, exploração e incerteza. Não haverá seleção posterior de semente para melhorar o teste.

Os cinco exemplos do Golden Set cobrem cold start, afinidade mista, canal, cliente novo e histórico alto. Os mesmos casos são testados automaticamente.

## Serviço e persistência

O serviço terá:

- `POST /recommend`: valida contexto e retorna ação, segmento, versão, médias posteriores, amostras e indicação de exploração;
- `POST /feedback`: registra resultado binário e atualiza a política local com idempotência;
- `GET /health`, `GET /metadata` e `GET /metrics`;
- `/docs` com o contrato OpenAPI;
- interface HTML/CSS/JavaScript na raiz, servida pelo próprio FastAPI.

SQLite guarda decisões e feedback. O snapshot da política fica em `state/policy.json`. Repetição do mesmo feedback não atualiza novamente; conflito é rejeitado. Dados usados na gravação ficam separados do experimento oficial.

## Operação local e nuvem

O Compose inicia `api` e `mlflow`; o perfil `monitoring` adiciona Prometheus e Grafana. Imagens têm versões fixadas, healthcheck, usuário sem privilégios e volumes locais.

Para a publicação complementar, a imagem é construída localmente, enviada ao Artifact Registry e executada no Cloud Run com `POLICY_MODE=readonly`. O endpoint de feedback é desabilitado nesse modo. Nenhum aprendizado público depende do filesystem efêmero do Cloud Run.

O README conterá a arquitetura conceitual AWS pedida no checklist: armazenamento, processamento, serving e observabilidade, sem provisionar conta ou serviço.

## Qualidade, Git e autoria da entrega

O código seguirá layout `src`, tipagem, validação, funções coesas, tratamento explícito de erros e comentários apenas para decisões ou invariantes. Identificadores serão em inglês e a documentação para avaliação em português. Não haverá emojis, textos dirigidos ao autor ou referências ao processo de construção dentro do código.

`.gitignore` exclui ambientes virtuais, dados brutos, bancos, snapshots locais, volumes, caches, credenciais, PDFs de aula e mídia. Evidências pequenas, notebooks, figuras e resultados consolidados entram no Git. `.dockerignore` impede que dados e materiais locais sejam copiados para a imagem.

Commits serão pequenos e coerentes. O histórico não será fabricado. Antes da publicação final serão conferidos clone limpo, notebooks reexecutáveis, links, testes, ausência de segredos, imagem e correspondência entre README, MLflow e API.

## Gravação e `video.txt`

O roteiro será fechado quando os resultados reais estiverem prontos. A gravação terá cerca de 4min50s:

1. problema e objetivo;
2. base, ações e recompensa;
3. baseline, Thompson Sampling e evidência;
4. recomendação e feedback na aplicação local;
5. Docker, MLflow e limitações.

O vídeo mostrará uma execução real, com estado preparado e informações pessoais ocultas. Após a publicação do vídeo, `video.txt` conterá a URL definitiva e será adicionado em commit próprio. O MP4 ficará fora do repositório. Não será colocado link fictício ou placeholder na entrega.

## Critérios de aceite

- EDA e notebook de experimento executam do início ao fim em clone limpo.
- Baseline, política adaptativa, cinco casos e métricas estão reproduzíveis.
- Testes cobrem política, replay, snapshot, feedback idempotente e API.
- `ruff` e `pytest` passam no CI.
- Docker Compose sobe a aplicação local e o MLflow quando o daemon Docker estiver disponível.
- API retorna recomendação válida e o feedback atualiza uma única vez.
- README explica dados, limitações, execução, MLOps, nuvem e vídeo.
- Cloud Run, se publicado, opera explicitamente em modo somente leitura.
- `video.txt` contém o link real antes da tag final do repositório.
