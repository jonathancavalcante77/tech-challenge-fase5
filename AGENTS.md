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
- Não misturar ferramentas de fases anteriores por hábito. Streamlit não faz parte desta solução.

## Escopo atual

A prioridade é concluir e revisar o projeto local. Não criar repositório remoto, não enviar ao GitHub, não preparar roteiro, não gravar vídeo e não criar `video.txt` até nova autorização explícita. A publicação real na GCP também está adiada. Artefatos e scripts locais de Cloud Run devem permanecer prontos.

As melhorias opcionais fazem parte da entrega local: MLflow, Prometheus, Grafana, dashboard, métricas operacionais e script de Cloud Run.

## Arquitetura fechada

- Python 3.11 ou 3.12, layout `src`.
- FastAPI serve API e interface web própria.
- Thompson Sampling Beta-Bernoulli contextual é a política oficial.
- A API usa `recommend`, o mesmo comportamento estocástico avaliado por replay sequencial.
- `config/policy_snapshot.json` contém o estado treinado inicial.
- Em modo `mutable`, SQLite é a fonte transacional de decisões, feedback e estado da política. `state/policy.json` é um espelho atômico.
- Em modo `readonly`, feedback é rejeitado e o snapshot não é alterado.
- Docker Compose executa API, MLflow e o registro automático do experimento. O perfil `monitoring` adiciona Prometheus e Grafana.
- Cloud Run deve usar `POLICY_MODE=readonly` e o snapshot incluído na imagem.

## Interpretação dos resultados

Resultados atuais com semente `2026`:

- baseline `no_email`: 0,007030;
- melhor ação fixa `mens_email`: 0,014763;
- Thompson Sampling: 0,013826;
- lift contra baseline: +0,006796;
- diferença contra melhor ação fixa: -0,000937;
- exploração: 18,47%.

A política adaptativa supera o baseline exigido. Não afirmar que supera a melhor ação fixa. Os intervalos se sobrepõem e são aproximações descritivas.

## Comandos de validação

```powershell
.\.venv\Scripts\python.exe -m ruff check src app scripts tests
.\.venv\Scripts\python.exe -m ruff format --check src app scripts tests
.\.venv\Scripts\python.exe -m pytest --cov=src --cov=app
.\.venv\Scripts\python.exe scripts/run_experiment.py
.\.venv\Scripts\python.exe scripts/build_golden_set.py
.\.venv\Scripts\python.exe scripts/execute_notebooks.py
docker compose config --quiet
docker compose up --build
docker compose --profile monitoring up --build
```

Antes de declarar conclusão, verificar que os dois notebooks têm todas as células executadas, outputs salvos e nenhum erro. Confirmar também API, feedback, reinício, MLflow, Prometheus e Grafana no ambiente Docker.

## Git e artefatos

- Não alterar histórico nem configurar remote nesta etapa.
- Dados brutos, `.venv`, bancos, volumes, estados mutáveis, caches, credenciais, PDFs e vídeos ficam fora do Git.
- Devem permanecer versionáveis: notebooks executados, `artifacts/experiment_summary.json`, `artifacts/golden_set.json`, figuras, snapshot treinado, código, testes e documentação.
- Não adicionar `aula-datathon/` nem materiais de aula.
