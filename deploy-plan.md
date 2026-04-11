# Docker Compose Deployment Plan

## Architecture

```
[browser]
    │
    ▼
[nginx - frontend :80]
    ├── /api, /static, /threads, /assistants  ──proxy──▶  [backend :8000]
    └── /*  (static React app)                                   │
                                                           [postgres :5432]
```

---

## Files to Create

### `agent_api/Dockerfile`

```dockerfile
FROM python:3.14-slim
WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock ./
RUN uv pip install --system --no-cache .

COPY . .

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `client/Dockerfile`

```dockerfile
# Stage 1: build
FROM node:22-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: serve
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### `client/nginx.conf`

```nginx
server {
  listen 80;

  location / {
    root /usr/share/nginx/html;
    try_files $uri $uri/ /index.html;
  }

  location ~ ^/(api|static|threads|assistants) {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }
}
```

### `docker-compose.yml` (project root — replaces `agent_api/docker-compose.yml`)

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: postgres
    ports:
      - "5431:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      retries: 5

  backend:
    build: ./agent_api
    ports:
      - "8000:8000"
    env_file:
      - ./agent_api/.env
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/postgres
    volumes:
      - static_files:/app/static
    depends_on:
      db:
        condition: service_healthy

  frontend:
    build: ./client
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  pgdata:
  static_files:
```

---

## Key Notes

- **DATABASE_URL** in the `environment:` block overrides the value in `.env` so it uses the `db` container hostname instead of `localhost`
- **Static files** (`/app/static`) are persisted via a named volume — this is where uploaded photos live (`STATIC_DIR` in `core/config.py`)
- **Secrets** (OPENAI_API_KEY, PMS creds, etc.) stay in `agent_api/.env`, loaded via `env_file`
- `agent_api/docker-compose.yml` can be deleted once the root-level compose is in place

---

## Usage

```bash
# Build and start everything
docker compose up --build

# Run migrations (first time or after schema changes)
docker compose run backend alembic upgrade head

# Access
# Frontend:  http://localhost
# Backend:   http://localhost:8000
```
