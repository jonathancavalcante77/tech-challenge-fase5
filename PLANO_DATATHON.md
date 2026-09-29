# Plano vigente — Datathon MLET Fase 5

## Objetivo

Entregar uma plataforma robusta de experimentação adaptativa para recomendação de campanhas, com evidência reproduzível, serviço local completo, MLOps e governança. O enunciado oficial permanece imutável em `POSTECH - MLET - DATATHON.pdf`; este arquivo registra decisões e estado de execução.

## Decisões fechadas

- execução principal local em Docker Compose;
- FastAPI com interface própria, sem Streamlit;
- Thompson Sampling Beta-Bernoulli contextual como política oficial;
- mesma política estocástica na avaliação sequencial e na API;
- `no_email` como controle escolhido pelo projeto e `mens_email` como melhor ação fixa de referência, escolhida no treino;
- SQLite como fonte transacional do aprendizado local;
- snapshot treinado como estado inicial obrigatório;
- MLflow, Prometheus e Grafana entregues localmente;
- script do Cloud Run pronto, com publicação real adiada;
- repositório privado no GitHub para revisão do autor; visibilidade pública, vídeo, roteiro e `video.txt` em etapa posterior.

## Estado local

| Frente | Estado | Evidência |
| --- | --- | --- |
| Dataset e checksum | Concluída | `data/source.json`, `src/datathon/data.py` |
| EDA | Concluída | notebook executado e `artifacts/figures/eda_actions.png` |
| Baseline e bandit | Concluída | notebook executado e resumo JSON |
| Política servida | Concluída | API usa Thompson Sampling carregado do snapshot |
| Demonstração para a banca | Redesenhada e validada localmente | linguagem em português, decisão explicada, comparação das ações, feedback controlado e layout responsivo |
| Golden Set | Concluída | cinco casos explicados no JSON, notebook e README |
| Persistência | Concluída | SQLite transacional, JSON atômico e recuperação testada |
| MLflow | Concluída localmente | registro deduplicado por chave de execução |
| Prometheus e Grafana | Concluída localmente | coleta saudável e dashboard provisionado |
| Docker | Concluída localmente | build, serviços, modo readonly, reinício e volumes validados |
| Cloud Run | Artefatos prontos | deploy real adiado |
| GitHub | Repositório privado de revisão | `jonathancavalcante77/tech-challenge-fase5`; abertura pública posterior |
| Vídeo | Pendente | gravação, roteiro e `video.txt` após avaliação do autor |

## Resultado oficial

Semente `2026`, 64.000 registros, divisão estratificada por ação:

- treino: 38.399;
- validação: 12.799;
- teste: 12.802;
- baseline `no_email`: 0,007030;
- melhor ação fixa `mens_email`: 0,014763;
- Thompson Sampling: 0,015466;
- lift absoluto contra controle: +0,008436;
- diferença contra melhor ação fixa: +0,000703;
- exploração: 22,29%;
- linhas casadas no replay de teste: 4.313.

A conclusão é ganho pontual contra o controle e contra a melhor ação histórica. Não afirmar que os intervalos comprovam superioridade estatística. `no_email` não foi determinado pelo professor; a escolha e seu limite estão justificados no README.

## Revisão com a aula de orientação

Foram lidos os dois arquivos autorizados: a transcrição da aula de 27/07/2026 e as dicas derivadas. O README concentra a matriz de aderência com timestamps, sem versionar os materiais da aula.

- Corrigida a ordem do replay: as partições estratificadas são embaralhadas antes do aprendizado sequencial. Semente, membros de cada partição, algoritmo e priors foram mantidos. Os resultados antigos foram substituídos.
- Snapshot vinculado aos parâmetros, à seleção e ao fingerprint de treino do resumo; o modo readonly ignora estado operacional antigo.
- Golden Set com cinco payloads visíveis, critérios independentes e avaliação capaz de reprovar uma resposta incoerente.
- MLflow identifica a evidência inteira por hash e admite nova execução quando o experimento muda ou a tentativa anterior falha.
- Cenário financeiro, recompensa, elegibilidade externa, retenção e descarte documentados; benchmark permanece explicitamente de varejo.
- A aula confirma que nuvem é conceitual, outra base pode ser justificada e um fluxo FastAPI é suficiente. Não exige migração para Streamlit ou novos serviços GCP.
- Repositório público e vídeo permanecem necessários para a entrega acadêmica; a cópia privada permite revisar o código antes da abertura pública.

## Validação local registrada

- 75 testes aprovados e 93% de cobertura em `src/datathon` e `app`;
- `ruff check` e `ruff format --check` aprovados;
- dois notebooks executados integralmente, com outputs salvos e nenhum erro;
- imagem executada com usuário não privilegiado `appuser`;
- API validada em modos `mutable` e `readonly`;
- atualização Bayesiana, idempotência, conflito e recuperação após reinício confirmados;
- MLflow com uma run finalizada por evidência, deduplicação por hash, artefato registrado e execução anterior preservada;
- snapshot `ts-contextual-v2-snapshot` ativo na demonstração; estado anterior arquivado localmente antes da atualização;
- cinco payloads do Golden Set validados também pela API no Docker;
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
- documentação corresponde aos resultados reais e distingue campos usados na decisão dos campos apenas registrados;
- interface apresenta a decisão em português, explica estimativas e exploração, e conclui o fluxo de feedback sem expor códigos internos;
- nenhuma credencial, base bruta, banco ou volume no Git.

## Revisão pré-publicação — 28/09/2026

A publicação está condicionada à avaliação do autor. Não foram criados remoto,
commit ou repositório GitHub nesta revisão.

- `.gitignore` revisado: materiais de `Aulas/`, todos os PDFs, formatos adicionais
  de bancos, credenciais usuais, backups, caches e arquivos do sistema ficam
  excluídos. O template `.env.example`, notebooks executados, figuras, snapshot,
  evidências e configuração de CI permanecem versionáveis. Os 34 casos de
  inclusão e exclusão verificados passaram.
- `.dockerignore` remove a exceção incorreta `!env.example` e exclui também
  formatos usuais de credenciais, bancos e arquivos compactados.
- A busca por assinaturas conhecidas de credenciais nos candidatos e nos cinco
  commits locais não encontrou ocorrências. A inspeção por nomes no histórico
  não encontrou bases CSV, bancos, PDFs, `.env` ou materiais de aula. Essas buscas
  não constituem garantia de ausência de todo formato possível de segredo.
- A revisão editorial não encontrou emojis ou comentários dirigidos ao autor
  no código da entrega. Comentários técnicos e docstrings foram preservados.
- Na revisão pré-publicação anterior, as correções passaram por 74 testes e 93%
  de cobertura tanto no ambiente de desenvolvimento quanto em uma instalação
  nova. A suíte atual passou com 75 testes após acrescentar a verificação da
  interface. Ruff e `pip check` passaram.
  A instalação nova emitiu um aviso de depreciação do SQLAlchemy usado pelo
  MLflow, sem falha nos testes de registro, recuperação ou deduplicação.

Correções e validações concluídas:

1. Contextos sem segmento presente na política são rejeitados pelo serviço antes
   da amostragem e retornam HTTP 422 na API. Os testes cobrem as três faixas de
   recência, os dois modos e a preservação do posterior e do histórico.
2. `DecisionStore` fecha as conexões explicitamente após commit ou rollback.
   Os testes cobrem sucesso, duplicação, conflito, decisão inexistente, liberação
   do arquivo e rollback do feedback quando a escrita do posterior falha.
3. A imagem foi construída a partir de uma cópia limpa, com volumes Docker novos.
   API, feedback, idempotência, conflito, reinício, MLflow, Prometheus e Grafana
   foram verificados. O modo readonly passou pelos cinco casos do Golden Set e
   rejeitou perfil sem treino sem alterar o snapshot.
4. A cópia limpa contém apenas os arquivos candidatos ao Git, com ambiente Python
   próprio e instalação nova de dependências. O download da base validou o
   checksum; resumo, snapshot e Golden Set reproduzidos correspondem exatamente
   aos JSONs da entrega. Os dois notebooks foram executados nessa instalação,
   com outputs completos e nenhum erro.
5. O workflow de CI inclui Ruff, formatação, suíte com cobertura de `src` e `app`
   e validação da configuração Compose. Sua execução no GitHub depende da futura
   publicação; os comandos Python foram verificados localmente.

As correções técnicas e a revisão da demonstração estão concluídas localmente.
A cópia de validação permanece em `.local/publication-check-20260928`, fora do Git;
ela não substitui o workspace. O autor ainda avaliará a experiência antes da publicação.

## Revisão da demonstração — 28/09/2026

O diagnóstico anterior apontou rótulos da base em inglês, códigos internos no
cartão principal, formulário que sugeria personalização por campos não usados,
feedback bruto e uma recomendação antiga ainda visível após mudar para um perfil
sem treino. O layout também era fraco em desktop e celular.

### Correções implementadas

- A página apresenta o Hillstrom como benchmark de varejo e o caso financeiro
  como hipótese. O fluxo visível segue perfil fictício, recomendação, comparação
  das campanhas e resultado observado.
- Recência e compras por categoria são entradas principais. Histórico de valor,
  cliente novo, canal e região ficam em seção adicional, com aviso de que não
  alteram a escolha. `Surburban` permanece como valor da base, mas o rótulo é
  `Suburbana`; os demais rótulos visíveis também estão em português.
- Cinco botões carregam os contextos fictícios do Golden Set. Toda ação continua
  sendo calculada por `/recommend`, sem copiar a ação salva no Golden Set.
- A área de decisão traduz o segmento, explica aproveitamento ou exploração
  conforme a resposta e esclarece quando a campanha difere da categoria da
  compra anterior. Um painel compara as três médias posteriores. A versão e os
  códigos internos ficam em detalhes recolhíveis.
- Qualquer alteração do formulário invalida a decisão exibida e impede que o
  feedback antigo pareça pertencer ao novo perfil. A combinação sem histórico
  nas duas categorias mostra um erro claro e não consulta uma política sem
  segmento treinado. Envio, sucesso, falha de rede, duplicação, modo `readonly`
  e nova recomendação têm estados próprios; os botões são bloqueados depois de
  registrar um resultado.
- O layout foi redesenhado com hierarquia, contraste, foco visível e adaptação
  para desktop e celular. O README descreve os dados usados, o comportamento
  estocástico e os limites das porcentagens.

### Verificação local

- 75 testes aprovados com 93% de cobertura; Ruff e sintaxe JavaScript aprovados;
- imagem Docker reconstruída; API, MLflow e Prometheus saudáveis, Grafana ativo;
- Chromium validou desktop e celular, ausência de rolagem horizontal, troca para
  perfil sem treino sem decisão residual, carregamento de perfil, feedback único,
  duplicação, conflito, ação sem e-mail, exploração, modo somente leitura e falha
  de rede;
- capturas e script de conferência em `.local/`, fora do Git.

O autor ainda avaliará o projeto no repositório privado antes de decidir sobre
a abertura pública e o vídeo.

## Revisão visual — 29/09/2026

A interface adotou a direção de ferramenta analítica. O formulário fica ao lado
da recomendação em desktop e acima dela no celular. A recomendação usa hierarquia
tipográfica sem cartão decorativo; as três estimativas aparecem como pontos na
mesma escala, com a ação escolhida identificada. IBM Plex Sans e IBM Plex Mono
substituem a aparência de template; cinzas e violeta contido substituem o ciano.
Perfis de referência e detalhes técnicos permanecem acessíveis em seções
recolhíveis. O tema claro/escuro respeita a preferência do sistema, permite
alternância manual e preserva a escolha localmente.

A segunda passada sobre capturas de 1440 e 390 pixels reduziu o título da página,
melhorou a leitura dos textos secundários e alinhou a escala do gráfico. O
contraste dos textos secundários no tema claro foi conferido acima de 4,5:1.
Playwright CLI produziu as capturas em `.local/ui-final-*.png`; o QA em Chromium
validou envio, erro, perfis de referência, feedback, modo somente leitura,
exploração, persistência do tema e ausência de rolagem horizontal entre 320 e
1024 pixels. Ruff, formatação, sintaxe JavaScript e 75 testes Python passaram.
As capturas são material local de revisão e ficam fora do Git.

## Publicação para revisão — 29/09/2026

O repositório `jonathancavalcante77/tech-challenge-fase5` foi criado como
**privado** para a revisão do autor. O `.gitignore` exclui dados brutos,
processados e formatos comuns de dataset/modelo, ambientes, bancos, estados,
volumes, credenciais, PDFs, materiais de aula, capturas locais e `video.txt`.
Notebooks executados, código, testes, resumo, Golden Set, figuras, snapshot e
documentação permanecem versionáveis. Não havia arquivo rastreado que violasse
essas regras; os cinco commits anteriores não continham PDFs, CSVs, bancos,
credenciais usuais, materiais de aula nem vídeo. A busca de assinaturas
conhecidas de tokens e chaves nos candidatos e no histórico não encontrou
ocorrências. Essa verificação não substitui revisão humana do repositório.

## Etapas posteriores

1. avaliar os arquivos e a apresentação no GitHub privado;
2. ajustar o projeto conforme a revisão;
3. autorizar a abertura pública quando estiver pronto para a entrega;
4. preparar o roteiro com base no sistema final e gravar o vídeo de até cinco minutos;
5. publicar o vídeo e adicionar o link real em `video.txt`;
6. avaliar se a demonstração em Cloud Run acrescenta valor.
