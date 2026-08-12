from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Playlist, Song
from app.schemas.song import SongPublic
from app.services.color import random_color

router = APIRouter(prefix="/api/v1/playlists", tags=["songs"])


@router.get(
    "/{playlist_id}/songs",
    response_model=list[SongPublic],
    summary="List songs in a playlist",
    description=(
        "Returns all songs belonging to the given playlist, ordered by sort_order ascending. "
        "Each song is given a randomly generated display color."
    ),
)
def list_songs_by_playlist(playlist_id: int, db: Session = Depends(get_db)) -> list[SongPublic]:
    playlist = db.get(Playlist, playlist_id)
    if playlist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")

    songs = (
        db.execute(
            select(Song).where(Song.playlist_id == playlist_id).order_by(Song.sort_order.asc())
        )
        .scalars()
        .all()
    )

    return [SongPublic.from_song(song, random_color()) for song in songs]
