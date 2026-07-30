# MaratonUSP Ensina 

Plataforma de estudos para maratona de programação: um backend Flask com
autenticação por sessão e um frontend com páginas de conteúdo e soluções.
O backend também serve as páginas do frontend, então tudo roda na mesma origem.

## Estrutura

```
projeto-maratona/
├── backend/                       # API Flask + serve o frontend
│   ├── tests/                     # testes automatizados
│   ├── app.py                     # aplicação principal
│   ├── pytest.ini                 # configuração do pytest
│   ├── requirements.txt     
│   └── requirements-dev.txt 
├── docs/
│   └── metrics/                   # documentação de métricas e milestones
├── frontend/                      # páginas (HTML + CSS + JavaScript)
│   ├── images/
│   │   └── favicon.png            # ícone exibido na aba do navegador
│   ├── auth-widget.css            # estilos do controle de login (tokens com fallback)
│   ├── auth-widget.js             # controle de login/logout compartilhado (botão + modal)
│   ├── base.css                   # cabeçalho/identidade visual compartilhada
│   ├── base.html                  # layout compartilhado (header, nav, footer, tema); páginas de conteúdo o estendem via Jinja
│   ├── calendar.css               # estilos do mini calendário
│   ├── calendar.js                # mini calendário: dias logados no mês + sequência (homepage)
│   ├── goals.css                  # estilos das metas
│   ├── goals.js                   # gerenciamento de metas: criação, listagem e exclusão
│   ├── heatmap.css                # estilos do heatmap
│   ├── heatmap.js                 # heatmap de atividade (itens concluídos por dia) no perfil
│   ├── index.css                  # estilos da homepage (com tokens de tema)
│   ├── index.html                 # homepage: login/registro + tema claro/escuro
│   ├── logout-message.css         # estilos da mensagem de logout
│   ├── logout-message.js          # exibe uma mensagem temporária após o logout
│   ├── pagina_admin.css           # estilos do painel administrativo
│   ├── pagina_admin.html          # painel administrativo: listar, criar, editar e excluir conteúdos
│   ├── pagina_admin_editar.css    # estilos da página de edição de conteúdos
│   ├── pagina_admin_editar.html   # página edição de conteúdos
│   ├── pagina_admin_novo.css      # estilos da página de criação de conteúdos
│   ├── pagina_admin_novo.html     # página de criação de conteúdos
│   ├── profile.css                # estilos do dashboard do usuário
│   ├── profile.html               # dashboard do usuário com heatmap, calendário, progresso e metas
│   ├── progress-bar.css           # estilos das barras de progresso do perfil e dos conteúdos
│   ├── progress-bar.js            # gera e atualiza as barras de progresso dos conteúdos
│   ├── progress.js                # controla e salva o progresso dos conteúdos
│   ├── solution.css               # estilos da página de solução dos problemas
│   ├── solucao.html               # página de solução de um problema
│   ├── topic.css                  # estilos específicos de topic.html
│   ├── topic.html                 # página de conteúdo genérica, estende base.html (renderiza GET /topics/<slug>)
│   ├── topics-list.css            # estilos da listagem de conteúdos em cartões
│   └── topics-list.html           # listagem em cartões: níveis (sem ?level=) ou tópicos de um nível (?level=<slug>)
├── scripts/                       # scripts auxiliares
│   └── metrics.sh                 # geração de métricas
├── .gitignore                     # arquivos ignorados pelo Git
├── PLAN.md                        # plano de entrega (PRs atômicos)
└── README.md
```


## Como rodar

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py                 # http://127.0.0.1:5000
```

Abra <http://127.0.0.1:5000> — a homepage (`index.html`) é servida em `/`, com
login/registro e alternância de tema claro/escuro (a preferência é salva no
`localStorage`). O banco SQLite (`users.db`) é criado automaticamente no primeiro
start e é ignorado pelo Git. Defina `SECRET_KEY` no ambiente para produção.

## Endpoints
 
| Método | Rota         | Descrição                                             |
| ------ | ------------ | ----------------------------------------------------- |
| GET    | `/`          | Homepage (`index.html`)                               |
| GET    | `/conteudo`  | Página de um tópico (`topic.html`); slug lido de `?topic=<slug>` no client |
| GET    | `/conteudos` | Listagem em cartões (`topics-list.html`): níveis, ou tópicos de um nível via `?level=<slug>` |
| GET    | `/health`    | Liveness — `{"status": "ok"}`                         |
| POST   | `/register`  | `{username, password}` → cria usuário; `409` se já existe, `400` se faltar campo |
| POST   | `/login`     | `{username, password}` → inicia a sessão; `401` se inválido |
| POST   | `/logout`    | Encerra a sessão                                      |
| GET    | `/me`        | Protegida — retorna o usuário logado, ou `401`        |
| GET    | `/progress`  | Protegida — progresso do usuário, mapa por `item_key` |
| POST   | `/progress`  | Protegida — salva `{item_key, kind, label, done}`     |
| GET    | `/activity`  | Protegida — registra o dia e retorna `{today, streak, days}` (dias logados no mês) |
| GET    | `/heatmap`   | Protegida — retorna `{today, counts}`: itens de progresso concluídos por dia |
| GET    | `/levels`    | Lista de níveis (`slug`, `title`) — alimenta o menu "Níveis" |
| GET    | `/levels/<slug>` | Um nível com seus tópicos (`slug`, `title`, `summary`); `404` se não existe |
| GET    | `/topics`    | Lista de tópicos de estudo (`slug`, `title`, `summary`) |
| GET    | `/topics/<slug>` | Um tópico com `references` e `problems`; `404` se não existe |


As senhas são guardadas com hash (`werkzeug.security`) e a sessão usa cookie
assinado do Flask.

## Frontend

As páginas em `frontend/` usam links relativos (CSS e navegação) e são servidas
pelo Flask na mesma origem da API — isso é o que faz o cookie de sessão do login
funcionar nas chamadas a `/me`. A homepage (`/`) é o ponto de entrada; as demais
páginas de conteúdo (ex.: `/conteudo?topic=busca_binaria`) também são servidas
pelo backend, via `render_template`, para poderem estender `base.html`.
 
O header, a nav e o footer ficam centralizados em `base.html` (`{% block content %}`
e `{% block extra_js %}` são os pontos de extensão); páginas como `index.html` e
`topic.html` estendem esse layout em vez de repetir a marcação. Qualquer página
de conteúdo que precise passar por `{% extends %}` do Jinja tem que ter uma rota
própria no Flask (não pode ser servida como arquivo estático puro).
 
O controle de login no canto superior (botão **Entrar** → modal, ou saudação +
**Sair**) é o mesmo em todas as páginas: vem de `auth-widget.js`/`auth-widget.css`.
Cada página só inclui esses dois arquivos e coloca `<span id="auth-controls"></span>`
no cabeçalho; o widget verifica a sessão (`GET /me`), injeta o modal e dispara um
evento `auth:change` que as páginas usam para mostrar/ocultar a área do usuário.
 
Na homepage, a área do usuário logado mostra um **mini calendário** do mês
(`calendar.js`): cada visita autenticada registra o dia (o backend grava em
`/login` e `/me`, e `GET /activity` devolve os dias do mês + a sequência), os
dias registrados aparecem marcados, o dia atual destacado e a **sequência** —
dias seguidos de acesso — logo abaixo. Sem login o calendário não aparece.

No perfil, a seção "Sua atividade" mostra um **heatmap** (`heatmap.js`) no
formato clássico: 7 linhas (uma por dia da semana), colunas são semanas
consecutivas, e o dia de hoje é sempre a última célula da última coluna. Os
dados vêm de `GET /heatmap`, que conta, por dia, quantos itens de progresso
foram marcados como concluídos (via `updated_at` da tabela `progress`) — cada
quadrado fica cinza sem atividade ou num de três tons de verde, mais escuro
quanto mais itens foram concluídos naquele dia. O número de semanas exibidas e
os limites de cada tom são constantes no topo do próprio `heatmap.js`, fáceis
de ajustar.
 
O conteúdo de estudo vem do banco (tabelas `levels`/`topics`/`topic_items`,
populadas por `SEED_LEVELS`/`SEED_CONTENT` em `app.py`): cada tópico pertence a
um nível (`level_id`), e `topic.html` lê o `slug` da query string (`/conteudo?topic=<slug>`),
busca `GET /topics/<slug>` e monta a página. Cada item já traz o `item_key` e o `label`
usados pelo `progress.js`, então os toggles persistem como nas páginas estáticas.
Cada problema também traz uma `difficulty` (`easy`/`medium`/`hard`) que vira a
barra de cor (verde/amarelo/vermelho) ao lado do título.


## Progresso de estudos

Nas páginas de conteúdo, os botões "Pendente/Lido" (referências) e "NA/AC"
(problemas) **persistem por usuário** quando há sessão ativa — sem login, eles
funcionam só visualmente. A lógica fica em `progress.js`: ao carregar a página ele
busca `GET /progress` e reflete o estado salvo; ao clicar, salva via `POST /progress`.

Cada botão declara três atributos que identificam o item de forma estável:

- `data-key` — id único, padrão `"<página>:<tipo>:<slug>"` (ex.: `busca_binaria:prob:roadworks`)
- `data-kind` — `ref` (referência/leitura) ou `problem` (resolvido)
- `data-label` — texto exibido no painel (ex.: `Problema 1 - Roadworks`)

A página `painel.html` lê `GET /progress` e mostra o que o usuário marcou, agrupado
em "Problemas resolvidos" e "Referências lidas".
