import os
# Override DATABASE_URL BEFORE any app imports so SQLAlchemy uses SQLite
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_temp.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-32chars")
os.environ.setdefault("GROK_API_KEY", "test-key")
os.environ.setdefault("SMTP_USERNAME", "test@test.com")
os.environ.setdefault("SMTP_PASSWORD", "testpass")

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DB_URL = "sqlite:///./test_temp.db"


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create tables once per test session."""
    from app.db.session import Base
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("./test_temp.db"):
        os.remove("./test_temp.db")


@pytest.fixture(scope="function")
def db(setup_test_db):
    from app.db.session import Base
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Clear all tables between tests
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db):
    from app.main import app
    from app.db.session import get_db

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db):
    from app.core.security import hash_password
    from app.models.models import User
    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        username="testuser",
        hashed_password=hash_password("testpass123"),
        full_name="Test User",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(client):
    resp = client.post("/api/v1/auth/register", json={
        "email": "auth@example.com",
        "username": "authuser",
        "password": "securepass123",
        "full_name": "Auth User",
    })
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
