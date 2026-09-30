# Contexto operacional do projeto

## Idioma e comunicação

- Comunicar-se com o usuário em português do Brasil.
- Manter nomes de APIs, comandos, bibliotecas e identificadores de código em inglês.
- Não usar emojis no código ou na documentação da entrega.
- Comentários de código devem explicar decisões, invariantes e limitações para avaliação acadêmica. Não inserir comentários dirigidos ao autor nem referências ao processo de autoria.

## Fontes e limites de leitura

- O enunciado oficial é `POSTECH - MLET - DATATHON.pdf` e deve permanecer imutável.
- O plano operacional é `PLANO_DATATHON.md`; atualize-o quando o estado técnico mudar.
- O documento principal para a banca é `README.md`.
- Não abrir, indexar ou usar arquivos da pasta `Aulas` nem de `aula-datathon` sem solicitação explícita do usuário.
- O usuário autorizou nesta revisão `aula-datathon/transcricao.md` e `aula-datathon/dicas.md`. A transcrição é fonte da orientação oral; dicas são interpretação secundária e seus números anteriores estão defasados. Essa autorização não inclui outros materiais de aula.
- Não misturar ferramentas de fases anteriores por hábito. Streamlit não faz parte desta solução.

## Escopo atual

A prioridade é revisar o projeto no repositório público `jonathancavalcante77/tech-challenge-fase5`, autorizado em 29/09/2026. A abertura pública foi autorizada explicitamente pelo autor. Não preparar roteiro, não gravar vídeo e não criar `video.txt` até nova autorização explícita. A publicação real na GCP também está adiada. Artefatos e scripts locais de Cloud Run devem permanecer prontos.

A interface de demonstração foi redesenhada em português como ferramenta analítica, com tipografia IBM Plex, temas claro/escuro, formulário centrado nas variáveis da política e comparação das três ações em escala comum. A versão de 29/09/2026 foi inspecionada com Playwright CLI em desktop e celular; as capturas finais estão em `.local/ui-final-*.png`, fora do Git. O QA em Chromium validou os fluxos principais, inclusive erro, feedback e persistência do tema. Perfis sem segmento treinado apagam a decisão anterior e exibem erro. O repositório público está acessível para avaliação do professor; o vídeo permanece pendente.

As melhorias opcionais fazem parte da entrega local: MLflow, Prometheus, Grafana, dashboard, métricas operacionais e script de Cloud Run.

## Arquitetura fechada

- Python 3.11 ou 3.12, layout `src`.
- FastAPI serve API e interface web própria.
- Thompson Sampling Beta-Bernoulli contextual é a política oficial.
- A API usa `recommend`, o mesmo comportamento estocástico avaliado por replay sequencial.
- `config/policy_snapshot.json` contém o estado treinado inicial.
- O snapshot é produzido a partir do resumo avaliado, com seed, priors e fingerprint de treino conferidos. Se a avaliação não selecionar Thompson Sampling, o gerador falha sem sobrescrever o snapshot.
- Cada partição estratificada é embaralhada deterministicamente; nunca alimentar replay com blocos ordenados pela ação histórica. Protocolo atual: `stratified-shuffled-replay-v2`.
- Em modo `mutable`, SQLite é a fonte transacional de decisões, feedback e estado da política. `state/policy.json` é um espelho atômico.
- Em modo `readonly`, o serviço carrega exclusivamente o snapshot, mesmo que exista estado mutable anterior; feedback é rejeitado.
- O serviço rejeita com HTTP 422 contextos sem segmento presente na política, antes de amostrar ou persistir. Não criar priors implicitamente na API para perfis sem suporte treinado.
- As conexões SQLite são fechadas explicitamente após commit ou rollback; falhas na persistência do posterior devem desfazer o feedback na mesma transação.
- Docker Compose executa API, MLflow e o registro automático do experimento. O perfil `monitoring` adiciona Prometheus e Grafana.
- Cloud Run deve usar `POLICY_MODE=readonly` e o snapshot incluído na imagem.

## Interpretação dos resultados

Resultados atuais com semente `2026`:

- baseline `no_email`: 0,007030;
- melhor ação fixa `mens_email`: 0,014763;
- Thompson Sampling: 0,015466;
- lift contra controle: +0,008436;
- diferença contra melhor ação fixa: +0,000703;
- exploração: 22,29%.

A política adaptativa apresenta ganho pontual contra o controle escolhido e a melhor ação fixa histórica. Não afirmar superioridade estatística: os intervalos do bandit e da melhor ação fixa se sobrepõem e são aproximações descritivas. `no_email` é escolha do projeto, não imposição do professor. Os números anteriores foram substituídos após corrigir a ordem do replay, sem procurar outra semente.

O Golden Set precisa continuar contendo cinco entradas fictícias e critérios independentes que possam reprovar a recomendação. `decision_makes_sense` não pode ser um literal incondicional. O MLflow deduplica pelo hash canônico do resumo completo e somente runs `FINISHED`.

## Comandos de validação

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m pytest --cov=src --cov=app
.\.venv\Scripts\python.exe scripts/run_experiment.py
.\.venv\Scripts\python.exe scripts/build_policy_snapshot.py
.\.venv\Scripts\python.exe scripts/build_golden_set.py
.\.venv\Scripts\python.exe scripts/execute_notebooks.py
docker compose config --quiet
docker compose up --build
docker compose --profile monitoring up --build
```

Antes de declarar conclusão, verificar que os dois notebooks têm todas as células executadas, outputs salvos e nenhum erro. Confirmar também API, feedback, reinício, MLflow, Prometheus e Grafana no ambiente Docker.

## Git e artefatos

- O remote `origin` aponta para o repositório público. Não reescrever histórico nem mudar a visibilidade sem autorização.
- `video.txt` permanece fora do Git até o vídeo estar gravado e o link ser fornecido pelo autor.
- Dados brutos, `.venv`, bancos, volumes, estados mutáveis, caches, credenciais, PDFs e vídeos ficam fora do Git.
- Devem permanecer versionáveis: notebooks executados, `artifacts/experiment_summary.json`, `artifacts/golden_set.json`, figuras, snapshot treinado, código, testes e documentação.
- Não adicionar `aula-datathon/` nem materiais de aula.
