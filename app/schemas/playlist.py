from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PlaylistPublic(BaseModel):
    """Frontend-facing playlist summary, used by the public playlist listing API."""

    id: int
    title: str
    writer: str

    model_config = ConfigDict(from_attributes=True)


class PlaylistBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    writer: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class PlaylistCreate(PlaylistBase):
    pass


class PlaylistUpdate(PlaylistBase):
    pass


class PlaylistAdmin(PlaylistBase):
    """Full playlist representation used in the admin panel."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
