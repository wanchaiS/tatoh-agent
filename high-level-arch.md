# Tatoh Resort — High-Level Architecture

## Overview

Single DigitalOcean Droplet running all services behind Cloudflare for CDN/SSL.

```
Internet
  │
  ▼
Cloudflare (CDN + SSL + image caching)
  │
  ▼
Nginx (reverse proxy)
  ├── /              → React SPA (static dist/)
  ├── /images/       → Local disk (static files, served by Nginx directly)
  └── /api/          → FastAPI (upstream: localhost:8000)
                          │
                          ├── LangGraph Agent (booking AI)
                          ├── PMS Client (Hoteliers Guru API)
                          └── PostgreSQL (localhost:5431)
```

---

## Components

### 1. Nginx (Reverse Proxy & Static Server)
- Serves the React client build (`dist/`) at `/`
- Serves images from `/var/www/tatoh/images/` at `/images/`
- Proxies `/api/` requests to FastAPI on `localhost:8000`
- Handles SSL termination (via Cloudflare or Certbot)
- Sets cache headers for static assets

### 2. FastAPI (Backend API + AI Agent)
- **Agent orchestration**: LangGraph multi-phase booking flow
- **LLM calls**: OpenAI (gpt-5.1-instant for discovery, gpt-4o-mini for room search)
- **PMS integration**: Hoteliers Guru API for real-time room availability & pricing
- **Streaming**: SSE for real-time chat responses
- **Thread management**: Stateful conversations via LangGraph checkpoints

### 3. React Client (Frontend)
- React 19 + Vite + Tailwind CSS
- LangGraph SDK for SSE streaming
- Built to static `dist/` and served by Nginx
- No Node.js runtime needed in production

### 4. PostgreSQL
- **LangGraph checkpoints**: Conversation state persistence (current)
- **Resort data**: Rooms, pricing, availability cache (future — migrate from Google Drive)
- **Booking records**: Guest bookings and history (future)
- Single instance, local to the droplet

### 5. Image Storage
- Images stored on local disk: `/var/www/tatoh/images/`
- Nginx serves directly (bypasses FastAPI — no performance impact on agent)
- Cloudflare caches globally (free CDN)
- FastAPI also mounts `/images` as StaticFiles (fallback / dev convenience)
- See `local-storage-setup.md` for detailed setup

### 6. Observability
- **LangSmith** (current choice): Auto-traces via LangChain/LangGraph integration
- Free tier sufficient for single-resort traffic
- Revisit Langfuse (self-hosted, open-source) if cost or data sovereignty becomes a concern

---

## Data Migration Path

| Data Source | Current | Target |
|---|---|---|
| Room info & amenities | Google Drive (markdown) | PostgreSQL |
| Room pricing | Google Sheets | PostgreSQL |
| Room images | Google Drive | Local disk (`/var/www/tatoh/images/`) |
| Availability | PMS API (live) | PMS API (no change) |
| Conversations | PostgreSQL (checkpoints) | PostgreSQL (no change) |

---

## Production Priorities

1. **Dockerize the stack** — Dockerfile for FastAPI, docker-compose for full stack (API + Postgres + Nginx)
2. **Nginx configuration** — Reverse proxy, static file serving, cache headers
3. **Image migration** — Move images from Google Drive to local disk
4. **Data migration** — Move room info/pricing from Google Sheets to PostgreSQL
5. **API security** — Rate limiting, authentication on endpoints
6. **Async PMS client** — Replace synchronous `requests` with `httpx` async
7. **Closing phase** — Implement booking confirmation flow (currently a stub)

---

## Open Questions (to discuss in detail later)

- Docker compose structure: single compose file or split by concern?
- Database schema design for rooms, pricing, bookings
- CI/CD pipeline (GitHub Actions → deploy to Droplet)
- Backup strategy for Postgres and images
- Domain/subdomain setup (API on same domain vs subdomain)
