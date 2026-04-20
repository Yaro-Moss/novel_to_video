
import pytest
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.database import Base, get_db
from app.models import User, Project, Task, ApiKey  # 导入所有模型
from app.core.security import get_password_hash


@pytest.fixture(scope="function")
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user in the database."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_token(client: TestClient, test_user: User):
    """Get an authentication token for the test user"""
    response = client.post(
        f"{settings.API_PREFIX}/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token_data = response.json()
    return token_data["access_token"]


@pytest.fixture(scope="function")
def authenticated_client(client, auth_token):
    """Create an authenticated test client."""
    client.headers["Authorization"] = f"Bearer {auth_token}"
    return client


@pytest.fixture(scope="function")
def temp_upload_dir():
    """Create a temporary directory for uploads."""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_upload_dir = settings.upload_dir_path
        settings.upload_dir_path = temp_dir
        os.makedirs(os.path.join(temp_dir, "uploads"), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, "output"), exist_ok=True)
        yield temp_dir
        settings.upload_dir_path = original_upload_dir
