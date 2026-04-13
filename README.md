### Start virtual env for python 

```bash
source .venv/bin/activate
```

### Install dependencies
```bash
uv sync
```

### Run langgraph development
```bash
langgraph dev
```

### Run FastApi production
```
uv run uvicorn api.main:app --reload
```### Database Migration
(Kepp in mind the script will use the DATABASE_URL in .env)
```bash
cd agent_api
make db-migrate
```

### Database Status
```bash
cd agent_api
make db-status
```

### Deploy Docker Locally (with .override.yml)
(Automatically exposes ports 80 and 5431)
```bash
docker compose up --build -d
```

### Deploy Docker in Production
(Secure via Cloudflare, requires `CLOUDFLARE_TUNNEL_TOKEN` in `.env`)
```bash
docker compose up --build -d
```

