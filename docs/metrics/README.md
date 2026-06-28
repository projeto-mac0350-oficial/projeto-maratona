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

| Milestone               | Data       | Arquivos | SLOC | CC média  | MI         | Pylint   | Relatório |
| ----------------------- | ---------- | -------- | ---- | --------- | ---------- | -------- | --------- |
| 1 — Autenticação        | 2026-06-28 | 1        | 87   | A (2,44)  | A (57,5)   | 9,05/10  | [milestone-1-auth.md](milestone-1-auth.md) |
| 2 — Progresso + painel  | _ao mesclar os PRs_ | | | | | | |

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
