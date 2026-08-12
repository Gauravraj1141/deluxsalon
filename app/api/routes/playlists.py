from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Playlist
from app.schemas.playlist import PlaylistPublic

router = APIRouter(prefix="/api/v1/playlists", tags=["playlists"])


@router.get(
    "",
    response_model=list[PlaylistPublic],
    summary="List all playlists",
    description="Returns every playlist with the minimal fields needed to render a playlist list.",
)
def list_playlists(db: Session = Depends(get_db)) -> list[Playlist]:
    return list(db.execute(select(Playlist).order_by(Playlist.id)).scalars().all())
