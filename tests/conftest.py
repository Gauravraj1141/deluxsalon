import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import security
from app.core.limiter import limiter
from app.db.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "test-password"


@pytest.fixture()
def test_engine():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(test_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture()
def client(test_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    security.settings.ADMIN_USERNAME = ADMIN_USERNAME
    security.settings.ADMIN_PASSWORD = ADMIN_PASSWORD
    limiter.reset()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def admin_client(client):
    response = client.post(
        "/admin/login",
        data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
        follow_redirects=False,
    )
    assert response.status_code == 303
    return client
