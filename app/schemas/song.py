from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from app.db.models import Song


class SongPublic(BaseModel):
    """Frontend-facing song representation returned by the public songs API.

    `video_id` is exposed to clients as `videoId`, and the numeric database id is
    serialized as a string to match the frontend contract.
    """

    id: str
    title: str
    artist: str
    video_id: str = Field(serialization_alias="videoId")
    duration: int
    color: str

    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def from_song(cls, song: "Song", color: str) -> "SongPublic":
        return cls(
            id=str(song.id),
            title=song.title,
            artist=song.artist,
            video_id=song.video_id,
            duration=song.duration,
            color=color,
        )


class SongBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    artist: str = Field(default="Unknown", max_length=255)
    video_id: str = Field(..., min_length=1, max_length=50)
    duration: int = Field(..., ge=0)
    sort_order: int = Field(default=0, ge=0)


class SongCreate(SongBase):
    pass


class SongUpdate(SongBase):
    pass


class SongAdmin(SongBase):
    """Full song representation used in the admin panel."""

    id: int

    model_config = ConfigDict(from_attributes=True)
