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
cd agent_api
uv run langgraph dev
```

### Run FastApi development
```bash
cd agent_api
uv run uvicorn api.main:app --reload
```

### Run client
```bash
cd client
npm run dev
```

### Database Status
```bash
make db-status
```

### Database Migrate
```bash
make db-migrate
```

### Deploy Docker Locally (with .override.yml)
(Automatically exposes ports 80 and 5431)
```bash
docker compose up --build -d
```


### Deploy Docker in Production

Cloudflare needs TUNNEL_TOKEN in .env at root
```bash
docker compose up -d cloudflared
```

DB (one time setup)
Make sure /agent_api/.env contains postgres username and password
```bash
docker compose up -d db
```
After deployed db, you will need to install the db schema
```bash
make db-status # to confirm that db is installed
make db-migrate
```

Now you can deploy client and api via make
```bash
make push # to build nad push images to DO
make deploy # to pull latest images and restart services on Droplet (configure ur droplet IP in Makefile)
```

