from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.admin.routes import router as admin_router
from app.api.routes import playlists, presence, songs
from app.core.config import settings
from app.core.limiter import limiter

app = FastAPI(
    title="Music Playlist API",
    description="Backend for a music playlist application: 2 public APIs plus an admin panel.",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="admin_session",
    https_only=settings.is_production,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SlowAPIMiddleware)

app.include_router(playlists.router)
app.include_router(songs.router)
app.include_router(presence.router)
app.include_router(admin_router)


@app.get("/health", tags=["health"], summary="Health check")
def health() -> dict[str, str]:
    return {"status": "ok"}
