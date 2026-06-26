# Projeto Maratona

Plataforma de estudos para maratona de programação: um backend Flask (autenticação)
e um frontend estático com páginas de conteúdo e soluções de problemas.

## Estrutura

```
projeto-maratona/
├── backend/                # API Flask
│   ├── app.py              # rotas, init_db(), auth (em construção)
│   └── requirements.txt
├── frontend/               # páginas estáticas (HTML + CSS)
│   ├── busca_binaria.html  # página de conteúdo (tema + referências + problemas)
│   ├── solucao.html        # página de solução de um problema
│   ├── base.css
│   ├── conteudo.css
│   └── solucao.css
├── PLAN.md                 # plano de entrega (PRs atômicos)
└── README.md
```

## Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py                 # http://127.0.0.1:5000
```

Endpoints disponíveis:

- `GET /health` — verificação de liveness (retorna `{"status": "ok"}`)

As rotas de autenticação (`/register`, `/login`, `/logout`, `/me`) estão planejadas
em [`PLAN.md`](PLAN.md). O banco SQLite (`users.db`) é criado automaticamente no
primeiro start e é ignorado pelo Git.

## Frontend

As páginas são estáticas — basta abrir os arquivos `.html` em `frontend/` no
navegador (ex.: `frontend/busca_binaria.html`). Os links entre páginas e folhas
de estilo são relativos à própria pasta `frontend/`.
