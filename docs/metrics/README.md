# Métricas de código — backend

Registro das métricas de **complexidade** e **manutenibilidade** do backend
(Flask), coletadas com **radon** e **pylint**, conforme pedido na disciplina
(aula de 23/06). A cada milestone salvamos um relatório e comentamos a evolução.

## Como são coletadas

- **CI (automático):** o workflow [`.github/workflows/metrics.yml`](../../.github/workflows/metrics.yml)
  roda a cada push na `main` e em cada PR. O relatório aparece na aba **Summary**
  da execução (GitHub → Actions) e fica disponível como artefato `metrics-report`.
- **Local:**
  ```bash
  cd backend && python -m venv venv && source venv/bin/activate
  pip install -r requirements.txt -r requirements-dev.txt
  cd .. && bash scripts/metrics.sh backend                       # imprime o relatório
  bash scripts/metrics.sh backend > docs/metrics/milestone-N.md  # salva um snapshot
  ```

## O que cada métrica indica

| Ferramenta  | Métrica                   | Leitura |
| ----------- | ------------------------- | ------- |
| `radon cc`  | Complexidade ciclomática  | nº de caminhos independentes; menor é mais simples. Faixas: **A** (1–5), **B** (6–10), **C** (11–20), **D** (21–30), **E** (31–40), **F** (41+). |
| `radon mi`  | Índice de manutenibilidade| 0–100; maior é mais fácil de manter. Rank **A** (melhor) a **C**. |
| `radon raw` | Métricas brutas           | LOC / SLOC / LLOC, comentários, linhas em branco. |
| `radon hal` | Halstead                  | volume / dificuldade / esforço a partir de operadores e operandos. |
| `pylint`    | Nota de qualidade         | análise estática com nota final *"rated at X/10"*. |

## Relatórios por milestone

Números do **backend inteiro** (o que o script mede). Nos milestones 1 e 2 isso era
só o `app.py`; a partir do 3 entram também os arquivos de teste.

| Milestone                       | Data       | Arquivos | SLOC | CC média  | MI            | Pylint   | Relatório |
| ------------------------------- | ---------- | -------- | ---- | --------- | ------------- | -------- | --------- |
| 1 — Autenticação                | 2026-06-28 | 1        | 87   | A (2,44)  | A (57,5)      | 9,05/10  | [milestone-1-auth.md](milestone-1-auth.md) |
| 2 — Progresso + painel          | 2026-06-28 | 1        | 143  | A (2,91)  | A (51,9)      | 9,25/10  | [milestone-2-progress.md](milestone-2-progress.md) |
| 3 — Testes, conteúdo, atividade | 2026-07-30 | 6        | 619  | A (3,00)  | A (42,8–94,1) | 8,56/10  | [milestone-3-conteudo-atividade.md](milestone-3-conteudo-atividade.md) |

> A cada entrega: rode o script (ou baixe o artefato do CI), salve
> `docs/metrics/milestone-N.md`, acrescente uma linha aqui e copie para a wiki.

## Interpretação (milestone 1)

O backend é hoje um **app Flask de arquivo único** (`backend/app.py`, 87 SLOC), e
as métricas refletem isso:

- **Complexidade baixa.** Complexidade ciclomática média **A (2,44)** — código
  simples e linear. Os únicos blocos acima de A são `login` **B (8)** e `register`
  **B (7)**, que concentram validação de entrada, consulta ao banco e os ramos de
  erro (400/401/409). Nenhum bloco chega a C, então não há funções "difíceis de
  testar".
- **Manutenibilidade boa, mas não alta.** Índice de manutenibilidade **A (57,5)**:
  está na melhor faixa (A), porém longe do topo da escala 0–100. Concentrar rotas,
  validação e SQL no mesmo módulo puxa o índice para baixo. O Halstead pequeno
  (volume ≈ 249, ~0,08 "bugs" estimados) confirma que o módulo ainda é enxuto.
- **Qualidade alta.** Pylint **9,05/10**. Os descontos são só de convenção —
  docstrings ausentes em alguns handlers (`health`, `register`, `login`, `logout`,
  `me`) e no módulo. Adicioná-las leva a nota para ~10 sem mexer na arquitetura.

### Relação com a arquitetura

A arquitetura monolítica de um arquivo é adequada ao tamanho atual e mantém as
métricas saudáveis. O ponto de atenção é o **MI**: como tudo vive em `app.py`, cada
nova rota soma complexidade e LOC ao mesmo módulo. Conforme o backend crescer
(endpoints de progresso, conteúdo, admin…), espera-se **CC e LOC subindo e o MI
caindo**. A refatoração natural — separar em módulos/blueprints (`auth`, `progress`,
acesso a banco) — distribui a complexidade e tende a **recuperar o MI**, mantendo o
pylint alto.

### Evolução esperada

Metas simples para acompanhar entre milestones:

- CC média no rank **A**; nenhum bloco pior que **C**.
- MI no rank **A**.
- Pylint **≥ 9/10**.

Compare a tabela acima a cada entrega e comente os desvios (ex.: uma função que
virou C, ou queda do MI ao adicionar features) — é exatamente a discussão de
engenharia de software pedida pela disciplina.

## Evolução — milestone 1 → 2

A entrega 2 adicionou os endpoints de progresso (`GET`/`POST /progress`) e a tabela
`progress`, tudo no mesmo `app.py`. O efeito nas métricas foi o **previsto** no
milestone 1:

| Métrica  | M1 (auth) | M2 (progresso) | Variação |
| -------- | --------- | -------------- | -------- |
| SLOC     | 87        | 143            | +56      |
| CC média | A (2,44)  | A (2,91)       | +0,47    |
| MI       | A (57,5)  | A (51,9)       | −5,6     |
| Pylint   | 9,05/10   | 9,25/10        | +0,20    |

- **MI caiu (57,5 → 51,9), como antecipado.** O backend continua sendo um único
  arquivo; cada rota nova soma volume (Halstead) e linhas ao mesmo módulo, e o índice
  de manutenibilidade reage a isso. Ainda está no rank **A**, mas a tendência confirma
  o ponto de atenção: ao crescer mais (conteúdo, admin), vale **separar em
  blueprints** (`auth`, `progress`, acesso a banco) para recuperar o MI.
- **CC subiu de leve (2,44 → 2,91).** O `set_progress` traz validação e o `UPSERT`,
  somando ramos; nada chega a C, então o código segue fácil de testar.
- **Pylint melhorou (9,05 → 9,25).** As funções novas já vieram com docstrings, então
  a proporção de avisos caiu. O teto continua sendo as poucas docstrings ausentes nos
  handlers antigos — um ajuste barato para chegar perto de 10.

**Leitura de engenharia:** as features novas mantiveram a saúde do código (CC e MI no
rank A, pylint acima de 9), mas a queda do MI é o primeiro sinal mensurável de que a
arquitetura de arquivo único tem prazo de validade. A próxima refatoração para módulos
deve ser avaliada quando o MI se aproximar do limite do rank A.

## Evolução — milestone 2 → 3

A entrega 3 juntou quatro frentes: **suíte de testes** (`backend/tests/`, 5 arquivos),
**API de conteúdo** (`GET /content/topics`, `GET /content/topics/<id>`, com dificuldade
dos problemas), **autenticação nas páginas de conteúdo** e **registro de atividade**
(`GET /activity`, dias de login + streak, que alimenta o mini calendário da home).
Tudo continua no mesmo `app.py`.

### Trajetória do `app.py` (série comparável)

Como os milestones 1 e 2 mediam só o `app.py`, a tabela abaixo isola esse arquivo para
a comparação ser justa:

| Métrica  | M1 (auth) | M2 (progresso) | M3 (conteúdo + atividade) | Variação M2 → M3 |
| -------- | --------- | -------------- | ------------------------- | ---------------- |
| SLOC     | 87        | 143            | 357                       | +214             |
| CC média | A (2,44)  | A (2,91)       | A (3,17)                  | +0,26            |
| MI       | A (57,5)  | A (51,9)       | A (42,8)                  | −9,1             |
| Pylint   | 9,05/10   | 9,25/10        | 9,57/10                   | +0,32            |

- **O `app.py` mais que dobrou (143 → 357 SLOC)** e o **MI caiu de novo (51,9 → 42,8)**,
  mantendo o ritmo de ~−9 por entrega. Continua no rank **A** — a faixa vai até 20 na
  escala do radon, então ainda há folga —, mas a tendência é monotônica e confirma o
  diagnóstico dos milestones anteriores: o arquivo único está no limite do que
  comporta bem.
- **A complexidade não acompanhou o tamanho (2,91 → 3,17).** O código novo é largamente
  *declarativo* — `CONTENT` (o catálogo de tópicos), `seed_content` e `_serialize_item`
  são dados e serialização, não ramificação. Os picos seguem sendo `login` **B (8)**,
  `set_progress` **B (8)** e `register` **B (7)**, os mesmos do milestone 1; o mais alto
  entre os novos é `get_topic` **B (6)**. **Nenhum bloco chega a C.**
- **Pylint subiu para 9,57/10** no `app.py`: só restam a docstring de módulo e cinco
  handlers antigos (`health`, `register`, `login`, `logout`, `me`) sem docstring.

### O que muda com a suíte de testes

Os testes entram nas métricas a partir daqui e explicam as diferenças entre a tabela do
backend inteiro e a série do `app.py`:

- **CC média do conjunto cai para A (3,00)**, abaixo dos 3,17 do `app.py`: são 65 blocos
  no total (contra 18 antes), e os testes são lineares. **Nenhum teste passa de B.**
- **MI dos testes é alto** (67,0 / 63,9 / 61,3 / 53,3 e 94,1 no `conftest.py`), o que
  puxa a média do projeto para cima — por isso a coluna MI da tabela mostra uma faixa,
  e não um número só.
- **Pylint do conjunto cai para 8,56/10** enquanto o do `app.py` sobe. A queda é quase
  toda `missing-function-docstring` nos testes, cujo nome já descreve o caso, mais dois
  avisos reais no `conftest.py` (`wrong-import-position`, `redefined-outer-name`,
  ambos consequência do `sys.path` ajustado para importar o app). É ruído de convenção,
  não dívida técnica — vale considerar um `.pylintrc` que relaxe `C0116` em
  `backend/tests/` para a nota voltar a medir o código de produção.

**Leitura de engenharia:** o projeto ganhou cobertura de testes e três features sem
piorar a testabilidade (CC estável, nada acima de B), e a qualidade estática do código
de produção melhorou. O sinal a acompanhar continua sendo o **MI do `app.py`**: três
entregas, três quedas (57,5 → 51,9 → 42,8). Se o próximo milestone repetir o padrão, a
separação em **blueprints** (`auth`, `content`, `progress`, `activity` + camada de
acesso ao banco) deixa de ser opcional — é a refatoração que redistribui volume e
recupera o índice.
