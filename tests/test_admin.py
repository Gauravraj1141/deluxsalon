def test_login_rejects_invalid_credentials(client):
    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_login_accepts_valid_credentials(client):
    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "test-password"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/playlists"


def test_admin_routes_require_login(client):
    response = client.get("/admin/playlists", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"


def test_create_and_update_playlist(admin_client):
    response = admin_client.post(
        "/admin/playlists/new",
        data={"title": "My Playlist", "writer": "Me", "description": "A description"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    playlist_id = int(response.headers["location"].rsplit("/", 1)[-1])

    response = admin_client.post(
        f"/admin/playlists/{playlist_id}/edit",
        data={"title": "Updated Title", "writer": "Me", "description": "A description"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    response = admin_client.get(f"/admin/playlists/{playlist_id}")
    assert response.status_code == 200
    assert "Updated Title" in response.text

    response = admin_client.get("/api/v1/playlists")
    assert response.json() == [{"id": playlist_id, "title": "Updated Title", "writer": "Me"}]


def test_create_update_delete_song(admin_client):
    response = admin_client.post(
        "/admin/playlists/new",
        data={"title": "Songs Playlist", "writer": "Me", "description": ""},
        follow_redirects=False,
    )
    playlist_id = int(response.headers["location"].rsplit("/", 1)[-1])

    response = admin_client.post(
        f"/admin/playlists/{playlist_id}/songs/new",
        data={
            "title": "Song A",
            "artist": "",
            "video_id": "abc123",
            "duration": 200,
            "sort_order": 1,
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    songs = admin_client.get(f"/api/v1/playlists/{playlist_id}/songs").json()
    assert len(songs) == 1
    assert songs[0]["title"] == "Song A"
    assert songs[0]["artist"] == "Unknown"
    song_id = int(songs[0]["id"])

    response = admin_client.post(
        f"/admin/playlists/{playlist_id}/songs/{song_id}/edit",
        data={
            "title": "Song A Updated",
            "artist": "Someone",
            "video_id": "abc123",
            "duration": 210,
            "sort_order": 1,
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    songs = admin_client.get(f"/api/v1/playlists/{playlist_id}/songs").json()
    assert songs[0]["title"] == "Song A Updated"
    assert songs[0]["artist"] == "Someone"

    response = admin_client.post(
        f"/admin/playlists/{playlist_id}/songs/{song_id}/delete", follow_redirects=False
    )
    assert response.status_code == 303

    songs = admin_client.get(f"/api/v1/playlists/{playlist_id}/songs").json()
    assert songs == []
