# Projeto Maratona

Plataforma de estudos para maratona de programação: um backend Flask com
autenticação por sessão e um frontend com páginas de conteúdo e soluções.
O backend também serve as páginas do frontend, então tudo roda na mesma origem.

## Estrutura

```
projeto-maratona/
├── backend/                # API Flask + serve o frontend
│   ├── app.py              # rotas, init_db(), auth (register/login/logout/me)
│   └── requirements.txt
├── frontend/               # páginas (HTML + CSS)
│   ├── index.html          # homepage: login/registro + tema claro/escuro
│   ├── index.css           # estilos da homepage (com tokens de tema)
│   ├── busca_binaria.html  # página de conteúdo (tema + referências + problemas)
│   ├── solucao.html        # página de solução de um problema
│   ├── painel.html         # dashboard: progresso do usuário logado
│   ├── progress.js         # persiste os toggles "lido/resolvido" por usuário
│   ├── base.css            # cabeçalho/identidade visual compartilhada
│   ├── conteudo.css
│   └── solucao.css
├── PLAN.md                 # plano de entrega (PRs atômicos)
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
| GET    | `/health`    | Liveness — `{"status": "ok"}`                         |
| POST   | `/register`  | `{username, password}` → cria usuário; `409` se já existe, `400` se faltar campo |
| POST   | `/login`     | `{username, password}` → inicia a sessão; `401` se inválido |
| POST   | `/logout`    | Encerra a sessão                                      |
| GET    | `/me`        | Protegida — retorna o usuário logado, ou `401`        |
| GET    | `/progress`  | Protegida — progresso do usuário, mapa por `item_key` |
| POST   | `/progress`  | Protegida — salva `{item_key, kind, label, done}`     |

As senhas são guardadas com hash (`werkzeug.security`) e a sessão usa cookie
assinado do Flask.

## Frontend

As páginas em `frontend/` usam links relativos (CSS e navegação) e são servidas
pelo Flask na mesma origem da API — isso é o que faz o cookie de sessão do login
funcionar nas chamadas a `/me`. A homepage (`/`) é o ponto de entrada; as demais
páginas (ex.: `/busca_binaria.html`) também são servidas pelo backend.

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
