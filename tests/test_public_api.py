import re

from app.db.models import Playlist, Song

HEX_COLOR_RE = re.compile(r"^#[0-9A-F]{6}$")


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_playlists_empty(client):
    response = client.get("/api/v1/playlists")
    assert response.status_code == 200
    assert response.json() == []


def test_list_playlists_returns_frontend_friendly_shape(client, db_session):
    playlist = Playlist(title="Punjabi Hits", writer="Writer Name")
    db_session.add(playlist)
    db_session.commit()

    response = client.get("/api/v1/playlists")
    assert response.status_code == 200
    assert response.json() == [{"id": playlist.id, "title": "Punjabi Hits", "writer": "Writer Name"}]


def test_songs_by_playlist_ordering_and_shape(client, db_session):
    playlist = Playlist(title="Test Playlist", writer="Writer")
    db_session.add(playlist)
    db_session.flush()

    db_session.add(
        Song(
            playlist_id=playlist.id,
            title="Second",
            artist="Artist 2",
            video_id="vid2",
            duration=100,
            sort_order=2,
        )
    )
    db_session.add(
        Song(
            playlist_id=playlist.id,
            title="First",
            artist="Artist 1",
            video_id="vid1",
            duration=50,
            sort_order=1,
        )
    )
    db_session.commit()

    response = client.get(f"/api/v1/playlists/{playlist.id}/songs")
    assert response.status_code == 200

    songs = response.json()
    assert [song["title"] for song in songs] == ["First", "Second"]

    first = songs[0]
    assert isinstance(first["id"], str)
    assert first["videoId"] == "vid1"
    assert "video_id" not in first
    assert HEX_COLOR_RE.match(first["color"])


def test_songs_playlist_not_found(client):
    response = client.get("/api/v1/playlists/999/songs")
    assert response.status_code == 404


def test_songs_empty_playlist(client, db_session):
    playlist = Playlist(title="Empty Playlist", writer="Writer")
    db_session.add(playlist)
    db_session.commit()

    response = client.get(f"/api/v1/playlists/{playlist.id}/songs")
    assert response.status_code == 200
    assert response.json() == []
