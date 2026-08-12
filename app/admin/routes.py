import json
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import (
    is_admin_logged_in,
    login_admin,
    logout_admin,
    require_admin,
    verify_admin_credentials,
)
from app.db.database import get_db
from app.db.models import Playlist, Song
from app.services.youtube import PlaylistFetchError, fetch_playlist_songs

router = APIRouter(prefix="/admin", tags=["admin"])

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


@router.get("/login")
def login_form(request: Request):
    if is_admin_logged_in(request):
        return RedirectResponse(url="/admin/playlists", status_code=303)
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login")
def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    if verify_admin_credentials(username, password):
        login_admin(request)
        return RedirectResponse(url="/admin/playlists", status_code=303)
    return templates.TemplateResponse(
        request, "login.html", {"error": "Invalid username or password."}, status_code=401
    )


@router.get("/logout")
def logout(request: Request):
    logout_admin(request)
    return RedirectResponse(url="/admin/login", status_code=303)


@router.get("")
def admin_root(_: None = Depends(require_admin)):
    return RedirectResponse(url="/admin/playlists", status_code=303)


# ---------------------------------------------------------------------------
# Playlists
# ---------------------------------------------------------------------------


@router.get("/playlists")
def list_playlists(
    request: Request, db: Session = Depends(get_db), _: None = Depends(require_admin)
):
    playlists = db.execute(select(Playlist).order_by(Playlist.id.desc())).scalars().all()
    return templates.TemplateResponse(
        request, "playlists.html", {"playlists": playlists}
    )


@router.get("/playlists/new")
def new_playlist_form(request: Request, _: None = Depends(require_admin)):
    return templates.TemplateResponse(
        request,
        "playlist_form.html",
        {"playlist": None, "error": None, "form_action": "/admin/playlists/new"},
    )


@router.post("/playlists/new")
def create_playlist(
    request: Request,
    title: str = Form(...),
    writer: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    title = title.strip()
    writer = writer.strip()
    if not title or not writer:
        return templates.TemplateResponse(
            request,
            "playlist_form.html",
            {
                "playlist": {"title": title, "writer": writer, "description": description},
                "error": "Title and writer are required.",
                "form_action": "/admin/playlists/new",
            },
            status_code=400,
        )

    playlist = Playlist(title=title, writer=writer, description=description.strip() or None)
    db.add(playlist)
    db.commit()
    return RedirectResponse(url=f"/admin/playlists/{playlist.id}", status_code=303)


@router.get("/playlists/{playlist_id}")
def playlist_detail(
    request: Request,
    playlist_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    playlist = db.get(Playlist, playlist_id)
    if playlist is None:
        return RedirectResponse(url="/admin/playlists", status_code=303)

    songs = (
        db.execute(
            select(Song).where(Song.playlist_id == playlist_id).order_by(Song.sort_order.asc())
        )
        .scalars()
        .all()
    )
    return templates.TemplateResponse(
        request, "playlist_detail.html", {"playlist": playlist, "songs": songs}
    )


@router.get("/playlists/{playlist_id}/edit")
def edit_playlist_form(
    request: Request,
    playlist_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    playlist = db.get(Playlist, playlist_id)
    if playlist is None:
        return RedirectResponse(url="/admin/playlists", status_code=303)
    return templates.TemplateResponse(
        request,
        "playlist_form.html",
        {
            "playlist": playlist,
            "error": None,
            "form_action": f"/admin/playlists/{playlist_id}/edit",
        },
    )


@router.post("/playlists/{playlist_id}/edit")
def update_playlist(
    request: Request,
    playlist_id: int,
    title: str = Form(...),
    writer: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    playlist = db.get(Playlist, playlist_id)
    if playlist is None:
        return RedirectResponse(url="/admin/playlists", status_code=303)

    title = title.strip()
    writer = writer.strip()
    if not title or not writer:
        return templates.TemplateResponse(
            request,
            "playlist_form.html",
            {
                "playlist": {
                    "id": playlist_id,
                    "title": title,
                    "writer": writer,
                    "description": description,
                },
                "error": "Title and writer are required.",
                "form_action": f"/admin/playlists/{playlist_id}/edit",
            },
            status_code=400,
        )

    playlist.title = title
    playlist.writer = writer
    playlist.description = description.strip() or None
    db.commit()
    return RedirectResponse(url=f"/admin/playlists/{playlist_id}", status_code=303)


@router.post("/playlists/{playlist_id}/delete")
def delete_playlist(
    playlist_id: int, db: Session = Depends(get_db), _: None = Depends(require_admin)
):
    playlist = db.get(Playlist, playlist_id)
    if playlist is not None:
        db.delete(playlist)
        db.commit()
    return RedirectResponse(url="/admin/playlists", status_code=303)


# ---------------------------------------------------------------------------
# Songs
# ---------------------------------------------------------------------------


@router.get("/playlists/{playlist_id}/songs/new")
def new_song_form(
    request: Request,
    playlist_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    playlist = db.get(Playlist, playlist_id)
    if playlist is None:
        return RedirectResponse(url="/admin/playlists", status_code=303)
    return templates.TemplateResponse(
        request,
        "song_form.html",
        {
            "playlist": playlist,
            "song": None,
            "error": None,
            "form_action": f"/admin/playlists/{playlist_id}/songs/new",
        },
    )


@router.post("/playlists/{playlist_id}/songs/new")
def create_song(
    request: Request,
    playlist_id: int,
    title: str = Form(...),
    artist: str = Form(""),
    video_id: str = Form(...),
    duration: int = Form(...),
    sort_order: int = Form(0),
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    playlist = db.get(Playlist, playlist_id)
    if playlist is None:
        return RedirectResponse(url="/admin/playlists", status_code=303)

    title = title.strip()
    video_id = video_id.strip()
    if not title or not video_id or duration < 0:
        return templates.TemplateResponse(
            request,
            "song_form.html",
            {
                "playlist": playlist,
                "song": {
                    "title": title,
                    "artist": artist,
                    "video_id": video_id,
                    "duration": duration,
                    "sort_order": sort_order,
                },
                "error": "Title, YouTube Video ID are required and duration must not be negative.",
                "form_action": f"/admin/playlists/{playlist_id}/songs/new",
            },
            status_code=400,
        )

    song = Song(
        playlist_id=playlist_id,
        title=title,
        artist=artist.strip() or "Unknown",
        video_id=video_id,
        duration=duration,
        sort_order=sort_order,
    )
    db.add(song)
    db.commit()
    return RedirectResponse(url=f"/admin/playlists/{playlist_id}", status_code=303)


@router.get("/playlists/{playlist_id}/songs/import")
def import_songs_form(
    request: Request,
    playlist_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    playlist = db.get(Playlist, playlist_id)
    if playlist is None:
        return RedirectResponse(url="/admin/playlists", status_code=303)
    return templates.TemplateResponse(
        request,
        "song_import.html",
        {"playlist": playlist, "error": None, "playlist_url": "", "songs_json": ""},
    )


@router.post("/playlists/{playlist_id}/songs/import/fetch")
def fetch_songs_from_url(
    request: Request,
    playlist_id: int,
    playlist_url: str = Form(...),
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    playlist = db.get(Playlist, playlist_id)
    if playlist is None:
        return RedirectResponse(url="/admin/playlists", status_code=303)

    playlist_url = playlist_url.strip()
    try:
        songs = fetch_playlist_songs(playlist_url)
    except PlaylistFetchError as exc:
        return templates.TemplateResponse(
            request,
            "song_import.html",
            {
                "playlist": playlist,
                "error": f"Couldn't fetch that playlist: {exc}",
                "playlist_url": playlist_url,
                "songs_json": "",
            },
            status_code=400,
        )

    return templates.TemplateResponse(
        request,
        "song_import.html",
        {
            "playlist": playlist,
            "error": None,
            "playlist_url": playlist_url,
            "songs_json": json.dumps(songs, indent=2, ensure_ascii=False),
        },
    )


@router.post("/playlists/{playlist_id}/songs/import")
def import_songs(
    request: Request,
    playlist_id: int,
    songs_json: str = Form(...),
    playlist_url: str = Form(""),
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    playlist = db.get(Playlist, playlist_id)
    if playlist is None:
        return RedirectResponse(url="/admin/playlists", status_code=303)

    def render_error(message: str, status_code: int = 400):
        return templates.TemplateResponse(
            request,
            "song_import.html",
            {
                "playlist": playlist,
                "error": message,
                "playlist_url": playlist_url,
                "songs_json": songs_json,
            },
            status_code=status_code,
        )

    try:
        data = json.loads(songs_json)
    except json.JSONDecodeError as exc:
        return render_error(f"Invalid JSON: {exc}")

    if not isinstance(data, list) or not data:
        return render_error("JSON must be a non-empty array of song objects.")

    next_sort_order = (
        db.execute(
            select(func.coalesce(func.max(Song.sort_order), 0)).where(
                Song.playlist_id == playlist_id
            )
        ).scalar()
        or 0
    ) + 1

    songs_to_create = []
    errors = []
    for index, item in enumerate(data):
        label = f"Song {index + 1}"
        if not isinstance(item, dict):
            errors.append(f"{label}: must be a JSON object.")
            continue

        title = str(item.get("title") or "").strip()
        video_id = str(item.get("video_id") or "").strip()
        artist = str(item.get("artist") or "").strip() or "Unknown"
        duration = item.get("duration", 0)

        if not title or not video_id:
            errors.append(f"{label}: 'title' and 'video_id' are required.")
            continue
        try:
            duration = int(duration)
        except (TypeError, ValueError):
            errors.append(f"{label}: 'duration' must be a number.")
            continue
        if duration < 0:
            errors.append(f"{label}: 'duration' must not be negative.")
            continue

        sort_order = item.get("sort_order")
        try:
            sort_order = int(sort_order) if sort_order is not None else next_sort_order
        except (TypeError, ValueError):
            errors.append(f"{label}: 'sort_order' must be a number.")
            continue
        next_sort_order = max(next_sort_order, sort_order + 1)

        songs_to_create.append(
            Song(
                playlist_id=playlist_id,
                title=title,
                artist=artist,
                video_id=video_id,
                duration=duration,
                sort_order=sort_order,
            )
        )

    if errors:
        return render_error(" ".join(errors))

    db.add_all(songs_to_create)
    db.commit()
    return RedirectResponse(url=f"/admin/playlists/{playlist_id}", status_code=303)


@router.get("/playlists/{playlist_id}/songs/{song_id}/edit")
def edit_song_form(
    request: Request,
    playlist_id: int,
    song_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    playlist = db.get(Playlist, playlist_id)
    song = db.get(Song, song_id)
    if playlist is None or song is None or song.playlist_id != playlist_id:
        return RedirectResponse(url="/admin/playlists", status_code=303)
    return templates.TemplateResponse(
        request,
        "song_form.html",
        {
            "playlist": playlist,
            "song": song,
            "error": None,
            "form_action": f"/admin/playlists/{playlist_id}/songs/{song_id}/edit",
        },
    )


@router.post("/playlists/{playlist_id}/songs/{song_id}/edit")
def update_song(
    request: Request,
    playlist_id: int,
    song_id: int,
    title: str = Form(...),
    artist: str = Form(""),
    video_id: str = Form(...),
    duration: int = Form(...),
    sort_order: int = Form(0),
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    playlist = db.get(Playlist, playlist_id)
    song = db.get(Song, song_id)
    if playlist is None or song is None or song.playlist_id != playlist_id:
        return RedirectResponse(url="/admin/playlists", status_code=303)

    title = title.strip()
    video_id = video_id.strip()
    if not title or not video_id or duration < 0:
        return templates.TemplateResponse(
            request,
            "song_form.html",
            {
                "playlist": playlist,
                "song": {
                    "id": song_id,
                    "title": title,
                    "artist": artist,
                    "video_id": video_id,
                    "duration": duration,
                    "sort_order": sort_order,
                },
                "error": "Title, YouTube Video ID are required and duration must not be negative.",
                "form_action": f"/admin/playlists/{playlist_id}/songs/{song_id}/edit",
            },
            status_code=400,
        )

    song.title = title
    song.artist = artist.strip() or "Unknown"
    song.video_id = video_id
    song.duration = duration
    song.sort_order = sort_order
    db.commit()
    return RedirectResponse(url=f"/admin/playlists/{playlist_id}", status_code=303)


@router.post("/playlists/{playlist_id}/songs/{song_id}/delete")
def delete_song(
    playlist_id: int,
    song_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    song = db.get(Song, song_id)
    if song is not None and song.playlist_id == playlist_id:
        db.delete(song)
        db.commit()
    return RedirectResponse(url=f"/admin/playlists/{playlist_id}", status_code=303)


@router.post("/playlists/{playlist_id}/songs/{song_id}/move")
def move_song(
    playlist_id: int,
    song_id: int,
    direction: str = Form(...),
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    songs = (
        db.execute(
            select(Song).where(Song.playlist_id == playlist_id).order_by(Song.sort_order.asc())
        )
        .scalars()
        .all()
    )

    index = next((i for i, s in enumerate(songs) if s.id == song_id), None)
    if index is not None:
        swap_index = index - 1 if direction == "up" else index + 1
        if 0 <= swap_index < len(songs):
            songs[index].sort_order, songs[swap_index].sort_order = (
                songs[swap_index].sort_order,
                songs[index].sort_order,
            )
            db.commit()

    return RedirectResponse(url=f"/admin/playlists/{playlist_id}", status_code=303)
