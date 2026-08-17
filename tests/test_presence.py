from app.db.models import Visitor


def test_heartbeat_sets_visitor_cookie_and_counts_self(client):
    response = client.post("/api/v1/presence/heartbeat")
    assert response.status_code == 200
    assert response.json() == {"count": 1}
    assert "vid" in response.cookies


def test_heartbeat_reuses_existing_visitor_cookie(client, db_session):
    first = client.post("/api/v1/presence/heartbeat")
    second = client.post("/api/v1/presence/heartbeat")

    assert first.json() == {"count": 1}
    assert second.json() == {"count": 1}
    assert db_session.query(Visitor).count() == 1


def test_heartbeat_counts_distinct_visitors(client):
    client.cookies.clear()
    client.post("/api/v1/presence/heartbeat")

    client.cookies.clear()
    response = client.post("/api/v1/presence/heartbeat")

    assert response.json() == {"count": 2}


def test_heartbeat_is_rate_limited(client):
    client.cookies.clear()
    for _ in range(10):
        response = client.post("/api/v1/presence/heartbeat")
        assert response.status_code == 200

    response = client.post("/api/v1/presence/heartbeat")
    assert response.status_code == 429
