# Plano vigente — Datathon MLET Fase 5

## Objetivo

Entregar uma plataforma robusta de experimentação adaptativa para recomendação de campanhas, com evidência reproduzível, serviço local completo, MLOps e governança. O enunciado oficial permanece imutável em `POSTECH - MLET - DATATHON.pdf`; este arquivo registra decisões e estado de execução.

## Decisões fechadas

- execução principal local em Docker Compose;
- FastAPI com interface própria, sem Streamlit;
- Thompson Sampling Beta-Bernoulli contextual como política oficial;
- mesma política estocástica na avaliação sequencial e na API;
- `no_email` como baseline obrigatório e `mens_email` como melhor ação fixa de referência;
- SQLite como fonte transacional do aprendizado local;
- snapshot treinado como estado inicial obrigatório;
- MLflow, Prometheus e Grafana entregues localmente;
- script do Cloud Run pronto, com publicação real adiada;
- GitHub, vídeo, roteiro e `video.txt` somente após a revisão local final.

## Estado local

| Frente | Estado | Evidência |
| --- | --- | --- |
| Dataset e checksum | Concluída | `data/source.json`, `src/datathon/data.py` |
| EDA | Concluída | notebook executado e `artifacts/figures/eda_actions.png` |
| Baseline e bandit | Concluída | notebook executado e resumo JSON |
| Política servida | Concluída | API usa Thompson Sampling carregado do snapshot |
| Golden Set | Concluída | cinco casos explicados no JSON, notebook e README |
| Persistência | Concluída | SQLite transacional, JSON atômico e recuperação testada |
| MLflow | Concluída localmente | registro deduplicado por chave de execução |
| Prometheus e Grafana | Concluída localmente | coleta saudável e dashboard provisionado |
| Docker | Concluída localmente | build, serviços, modo readonly, reinício e volumes validados |
| Cloud Run | Artefatos prontos | deploy real adiado |
| GitHub e vídeo | Adiados por decisão do autor | executar após nova revisão |

## Resultado oficial

Semente `2026`, 64.000 registros, divisão estratificada por ação:

- treino: 38.399;
- validação: 12.799;
- teste: 12.802;
- baseline `no_email`: 0,007030;
- melhor ação fixa `mens_email`: 0,014763;
- Thompson Sampling: 0,013826;
- lift absoluto contra baseline: +0,006796;
- diferença contra melhor ação fixa: -0,000937;
- exploração: 18,47%;
- linhas casadas no replay de teste: 4.242.

A conclusão autorizada é que a política adaptativa supera o baseline obrigatório. Não afirmar que supera a melhor ação fixa nem que os intervalos comprovam superioridade estatística.

## Validação local registrada

- 25 testes aprovados e 90% de cobertura em `src/datathon` e `app`;
- `ruff check` e `ruff format --check` aprovados;
- dois notebooks executados integralmente, com outputs salvos e nenhum erro;
- imagem executada com usuário não privilegiado `appuser`;
- API validada em modos `mutable` e `readonly`;
- atualização Bayesiana, idempotência, conflito e recuperação após reinício confirmados;
- MLflow com uma única run finalizada, deduplicação e artefato registrado;
- target da API saudável no Prometheus e dashboard `Adaptive Offers` carregado no Grafana;
- sintaxe do script de Cloud Run e configuração do Docker Compose aprovadas.

## Critérios para a próxima revisão

- `ruff check` e `ruff format --check` sem ocorrências;
- suíte de testes completa aprovada;
- notebooks com todas as células executadas e sem erros;
- artefatos compactos correspondentes ao código atual;
- imagem Docker construída;
- API inicia de volume vazio com o snapshot treinado;
- feedback é idempotente, concorrente e persiste após reinício;
- MLflow recebe um run sem duplicação;
- Prometheus coleta a API e Grafana carrega o dashboard;
- documentação corresponde aos resultados reais;
- nenhuma credencial, base bruta, banco ou volume no Git.

## Etapas posteriores, fora do escopo atual

1. executar nova revisão completa contra o PDF oficial;
2. revisar arquivos que entrarão no repositório público;
3. criar e enviar o repositório GitHub;
4. preparar o roteiro com base no sistema final;
5. gravar vídeo de até cinco minutos;
6. publicar o vídeo e adicionar o link real em `video.txt`;
7. avaliar se a demonstração em Cloud Run acrescenta valor.
