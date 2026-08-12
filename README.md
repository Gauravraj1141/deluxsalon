# Music Playlist Backend

A small, production-ready FastAPI backend for a music playlist app: two public read APIs for the
frontend, a session-authenticated admin panel for managing playlists/songs, PostgreSQL storage via
SQLAlchemy + Alembic, and Docker/GitHub Actions for shipping to GHCR.

## Project structure

```text
app/
├── main.py                  # FastAPI app, middleware, router wiring, /health
├── core/
│   ├── config.py            # Settings loaded from environment / .env
│   └── security.py          # Admin credential check + session auth dependency
├── db/
│   ├── database.py          # Engine, session factory, get_db dependency
│   └── models.py            # Playlist, Song SQLAlchemy models
├── schemas/
│   ├── playlist.py          # Pydantic schemas for playlists
│   └── song.py               # Pydantic schemas for songs (videoId alias, str id, color)
├── api/routes/
│   ├── playlists.py         # GET /api/v1/playlists
│   └── songs.py              # GET /api/v1/playlists/{id}/songs
├── admin/
│   ├── routes.py            # Admin auth + playlist/song CRUD routes
│   └── templates/           # Jinja2 templates for the admin UI
└── services/
    └── color.py             # Random hex color generator

alembic/                     # Migrations (env.py, versions/)
alembic.ini
seed.py                      # Inserts example playlist + songs
tests/                       # pytest suite (public API + admin)
Dockerfile
docker-compose.yml
.github/workflows/docker.yml # Build & push to GHCR on push to main
```

## Database

Two tables only:

- **`playlists`** — `id, title, writer, description, created_at, updated_at`
- **`songs`** — `id, playlist_id (FK → playlists.id, ON DELETE CASCADE), title, artist, video_id, duration, sort_order, created_at, updated_at`, indexed on `playlist_id`

Deleting a playlist deletes its songs (DB-level `ON DELETE CASCADE`, mirrored by the ORM
relationship). `color` is **not** stored — it's generated randomly on every response to the songs
API.

## Local development

1. Copy the environment template and fill in real values:

   ```bash
   cp .env.example .env
   ```

2. Start Postgres + the backend:

   ```bash
   docker compose up -d
   ```

3. Run database migrations:

   ```bash
   docker compose exec backend alembic upgrade head
   ```

4. (Optional) Insert example seed data — one playlist ("Punjabi Hits") with 8 songs:

   ```bash
   docker compose exec backend python seed.py
   ```

5. Visit:
   - API docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health
   - Admin panel: http://localhost:8000/admin/login

To stop the stack: `docker compose down` (add `-v` to also drop the Postgres volume).

### Running without Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/music_db
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Running tests

Tests run against an in-memory SQLite database (no Postgres required) via a `get_db` dependency
override:

```bash
pip install -r requirements-dev.txt
pytest
```

Covers: listing playlists, listing songs by playlist (ordering, `videoId`/color/id shape), 404 for
an unknown playlist, an empty playlist returning `[]`, admin login (valid/invalid), admin routes
requiring login, and playlist/song create/update/delete.

## Public API

| Method | Path                                  | Description                                   |
| ------ | -------------------------------------- | ---------------------------------------------- |
| GET    | `/api/v1/playlists`                    | List all playlists (`id`, `title`, `writer`)  |
| GET    | `/api/v1/playlists/{playlist_id}/songs` | Songs in a playlist, ordered by `sort_order`  |
| GET    | `/health`                              | Health check — `{"status": "ok"}`             |

Example song response:

```json
[
  {
    "id": "1",
    "title": "36",
    "artist": "Unknown",
    "videoId": "GmytqWwPazE",
    "duration": 239,
    "color": "#4FA7C9"
  }
]
```

`videoId` is aliased from the `video_id` database column, `id` is serialized as a string, and
`color` is a randomly generated hex code produced on every request — it is never persisted.

Interactive docs are available at `/docs` (Swagger UI) and `/openapi.json` (OpenAPI schema).

## Admin panel

Visit `/admin/login`, sign in with `ADMIN_USERNAME` / `ADMIN_PASSWORD` from your `.env`, then manage
playlists and songs at `/admin/playlists`. All `/admin/*` routes (other than the login page) require
an authenticated session — a signed cookie set via `SECRET_KEY`. Unauthenticated requests are
redirected to `/admin/login`. Public API routes are never gated by this session.

From the admin UI you can: create/edit/delete playlists, view a playlist's songs, add/edit/delete
songs, and reorder songs with the ↑/↓ controls (which swap `sort_order` between adjacent songs).

## Docker

Build the image directly:

```bash
docker build -t playlist-backend .
```

Run it (pointing at a Postgres instance you already have):

```bash
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+psycopg://postgres:postgres@<postgres-host>:5432/music_db \
  -e ADMIN_USERNAME=admin \
  -e ADMIN_PASSWORD=change-me \
  -e SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))") \
  playlist-backend
```

`docker-compose.yml` runs `backend` + `postgres` together. Postgres data is persisted in the named
volume `postgres_data` and is **not** exposed to the host — only the `backend` service can reach it,
via `postgres:5432` on the internal Docker network.

## Environment variables

See `.env.example`:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@postgres:5432/music_db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-this-password
SECRET_KEY=change-this-secret-key
APP_ENV=production
```

Never commit a real `.env` — it's already covered by `.gitignore`.

## GitHub Actions + GHCR

`.github/workflows/docker.yml` runs on every push to `main`: it checks out the repo, logs in to
GHCR using the built-in `GITHUB_TOKEN` (no separate registry secret needed), builds the image, and
pushes it tagged as both:

```text
ghcr.io/<github-username>/<repository-name>:latest
ghcr.io/<github-username>/<repository-name>:<commit-sha>
```

(repository owner/name are lowercased automatically, as GHCR requires). The job runs with the
minimum permissions needed: `contents: read`, `packages: write`.

If your repository is private, make sure the package's visibility/access is configured in GitHub
Package settings so your VPS can pull it (either make the package public, or `docker login ghcr.io`
on the VPS with a personal access token that has `read:packages`).

## Deploying on a VPS with Caddy

Target architecture:

```text
VPS
├── Caddy            (reverse proxy + TLS)
├── FastAPI container (backend, listens on 0.0.0.0:8000)
└── PostgreSQL container (internal only)
```

1. On the VPS, create a `docker-compose.yml` based on this repo's, but:
   - Pull the built image instead of building locally: `image: ghcr.io/<owner>/<repo>:latest`
     (add `docker login ghcr.io` first if the package is private).
   - Either drop the `ports: ["8000:8000"]` mapping on `backend` (if Caddy joins the same Docker
     network and reaches it at `backend:8000`), or keep it bound to localhost only
     (`127.0.0.1:8000:8000`) if Caddy runs outside Docker.
2. Add Caddy as a service on the same Docker network (or run it separately and attach it to this
   compose network), with a `Caddyfile` like:

   ```caddyfile
   api.my-domain.com {
       reverse_proxy backend:8000
   }
   ```

3. Run migrations after deploying: `docker compose exec backend alembic upgrade head`.
4. (Optional) seed data: `docker compose exec backend python seed.py`.

Caddy handles TLS termination and proxies `api.my-domain.com` to the FastAPI container on port
`8000`, which always binds to `0.0.0.0` so it's reachable from other containers on the network.
