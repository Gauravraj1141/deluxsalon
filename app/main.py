from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.admin.routes import router as admin_router
from app.api.routes import playlists, songs
from app.core.config import settings

app = FastAPI(
    title="Music Playlist API",
    description="Backend for a music playlist application: 2 public APIs plus an admin panel.",
    version="1.0.0",
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="admin_session",
    https_only=settings.is_production,
)

app.include_router(playlists.router)
app.include_router(songs.router)
app.include_router(admin_router)


@app.get("/health", tags=["health"], summary="Health check")
def health() -> dict[str, str]:
    return {"status": "ok"}
