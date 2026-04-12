# Admin Login System for /knowledge

## Context
Protect `/knowledge/**` routes for staff-only access. No PaaS. ≤10 users.
Clients never log in — chat persists via randomId in localStorage (separate concern).

**Approach:** JWT in httpOnly cookie (stateless, no Redis). Credentials in env vars (no DB migration). bcrypt password hashes. Rolling 10-min session via silent refresh.

## JWT Algorithm: HS256 (symmetric)
Chosen deliberately for this use case. Single secret signs + verifies — acceptable because:
- No external services need to verify tokens
- No microservices sharing tokens
- Internal staff tool only

Downside acknowledged: secret leak = unlimited token forgery. Mitigate: strong random secret (64+ hex chars), never commit to git.

## Session Strategy: Rolling 10-min window
Token expiry = 10 minutes. Frontend silently calls `POST /api/auth/refresh-token` on 401 to get a new cookie. Active users stay logged in indefinitely. Idle 10+ min → re-login required.

```
Request → 401 → POST /refresh-token
                    ├── 200 → retry original request
                    └── 401 → redirect /login
```

Non-401 errors (500, network) propagate to the TanStack Router error component — not the login page.

## Hosting: Same Machine (same-origin)
Client and server served via nginx reverse proxy on same domain (e.g. `tatoh.com`, `tatoh.com/api`).

Consequences:
- **CORS**: not required for production — same origin. Dev-only, explicit origin (wildcard + credentials is rejected by browsers).
- **SameSite**: use `Strict` in prod (same origin, no cross-site requests needed)
- **Secure**: required in prod (HTTPS). Dev can skip.
- Cookie config driven by `ENVIRONMENT=production` flag in `.env`

Cookie set logic:
```python
is_prod = settings.environment == "production"
response.set_cookie(
    key="session",
    value=token,
    httponly=True,
    samesite="strict" if is_prod else "lax",
    secure=is_prod,
    path="/",
)
```

---

## Offboarding
Remove user's `ADMIN_USER_*` env var + rotate `JWT_SECRET` + redeploy.
Existing tokens fail signature check. Refresh also fails. User hits `/login`, credentials rejected.
**Rotation logs everyone out** — inform remaining staff before doing it.

---

## Data Flow
Login form → `POST /api/auth/login` → bcrypt verify against env-var map → sign JWT (10 min) → `Set-Cookie: session=<jwt>; HttpOnly; SameSite=Strict` → frontend `fetchMe()` → TanStack Router `beforeLoad` guard → on 401: try refresh → if refresh 401: redirect `/login`.

---

## Backend

### 1. Add deps
`PyJWT`, `passlib[bcrypt]`

(Not `python-jose` — has active CVEs: CVE-2024-33664, algorithm confusion attacks.)

### 2. `agent_api/core/config.py`
Add to `Settings`:
```python
jwt_secret: str = Field(alias="JWT_SECRET")
jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
jwt_expire_minutes: int = Field(default=10, alias="JWT_EXPIRE_MINUTES")
environment: str = Field(default="development", alias="ENVIRONMENT")
```

### 3. New package: `agent_api/api/auth/`

**`schemas.py`** — `LoginRequest(username, password)`, `UserInfo(username)`

**`service.py`** — `AuthService`:
- `_load_users() -> dict[str, str]`: scan `os.environ` for `ADMIN_USER_*` prefix → `{"alice": "$2b$12$..."}`. Fail fast at startup if no users found.
- `verify_credentials(username, password) -> bool`
- `create_token(username) -> str` (PyJWT, HS256, 10-min exp)
- `decode_token(token) -> str | None` (returns username or None on any error/expiry)

**`router.py`** — endpoints:
- `POST /api/auth/login` — bcrypt verify → set httpOnly cookie on success
- `POST /api/auth/logout` — clear cookie (max-age=0)
- `POST /api/auth/refresh-token` — read `session` cookie → `decode_token` → if valid issue new 10-min token → set cookie; if invalid/expired → 401
- `GET /api/auth/me` — returns `UserInfo` (protected by `require_auth`)

### 4. `agent_api/api/dependencies.py`
Add `require_auth(request: Request) -> str`:
- reads `request.cookies.get("session")`
- decodes JWT, returns username or raises 401

### 5. `agent_api/api/main.py`
- Register `auth_router`
- Fix CORS: dev-only, explicit origin:
  ```python
  if settings.environment != "production":
      app.add_middleware(
          CORSMiddleware,
          allow_origins=["http://localhost:5173"],
          allow_credentials=True,
          allow_methods=["*"],
          allow_headers=["*"],
      )
  ```

### 6. `.env` additions
```
JWT_SECRET=<64-char hex>
ENVIRONMENT=development  # set "production" on server

# One var per user — no parsing ambiguity
ADMIN_USER_ALICE=$2b$12$...
ADMIN_USER_BOB=$2b$12$...

# Offboarding: remove user var + rotate JWT_SECRET + redeploy
```
Generate hash: `python -c "from passlib.hash import bcrypt; print(bcrypt.hash('mypass'))"`

---

## Frontend

### 7. `client/src/lib/auth.ts`
- `authQueryKey = ['auth', 'me']`
- `fetchMe()` — GET `/api/auth/me`
- `refreshToken()` — POST `/api/auth/refresh-token`
- `fetchWithRefresh(fn)` — calls `fn()`, on 401 tries `refreshToken()`, retries `fn()`, if still 401 throws
- export login/logout mutation helpers

### 8. `client/src/routes/login.tsx`
- New route at `/login`
- username + password form
- On success → `router.navigate({ to: '/knowledge' })`
- Inline error on 401

### 9. `client/src/routes/knowledge/route.tsx`
Add `beforeLoad` guard:
```ts
beforeLoad: async ({ context }) => {
  try {
    await context.queryClient.fetchQuery({
      queryKey: authQueryKey,
      queryFn: fetchMe,
      staleTime: 60_000,
    })
  } catch (e) {
    if (isUnauthorized(e)) {
      try {
        await refreshToken()
        await context.queryClient.fetchQuery({ queryKey: authQueryKey, queryFn: fetchMe })
      } catch {
        throw redirect({ to: '/login' })
      }
    }
    throw e  // non-401 → error component
  }
}
```

### 10. KnowledgeLayout — logout button
Call logout mutation → invalidate `authQueryKey` → navigate to `/login`

---

## New Files
| Path | Purpose |
|---|---|
| `agent_api/api/auth/__init__.py` | Package marker |
| `agent_api/api/auth/schemas.py` | Pydantic models |
| `agent_api/api/auth/service.py` | Bcrypt verify + JWT sign/decode + user loading |
| `agent_api/api/auth/router.py` | Auth endpoints incl. refresh-token |
| `client/src/lib/auth.ts` | Query key + fetch helpers + refresh logic |
| `client/src/routes/login.tsx` | Login page |

## Modified Files
| Path | Change |
|---|---|
| `agent_api/core/config.py` | Add jwt/environment fields |
| `agent_api/api/dependencies.py` | Add `require_auth` |
| `agent_api/api/main.py` | Register router, fix CORS (dev-only, explicit origin) |
| `client/src/routes/knowledge/route.tsx` | Add `beforeLoad` guard with refresh logic |

---

## Verification
1. `POST /api/auth/login` valid creds → 200 + `Set-Cookie: session=<jwt>; HttpOnly`
2. `GET /api/auth/me` no cookie → 401
3. `GET /api/auth/me` with cookie → 200 `{"username": "alice"}`
4. Wait 10 min → `GET /api/auth/me` → 401 → `POST /api/auth/refresh-token` → 401 (confirms expiry)
5. Active session: `POST /api/auth/refresh-token` within 10 min → 200 + new cookie
6. Navigate `/knowledge` logged out → redirects `/login`
7. Login → `/knowledge` accessible
8. Logout → cookie cleared → `/knowledge` redirects
9. Chat on `/` works without auth
10. Server 500 on `/api/auth/me` → error component shown (not login redirect)
11. Offboarding: remove `ADMIN_USER_ALICE` + rotate `JWT_SECRET` → token invalid → refresh fails → login → credentials rejected
