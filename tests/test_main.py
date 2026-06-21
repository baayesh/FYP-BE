import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.core.database import get_db, Base

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_read_main():
    response = client.get("/api/v1/")
    assert response.status_code == 404  # No root endpoint defined

def test_auth_endpoints_exist():
    """Test that authentication endpoints are accessible"""
    # These should return 422 (validation error) for empty request bodies
    response = client.post("/api/v1/auth/login")
    assert response.status_code == 422
    
    response = client.post("/api/v1/auth/register")
    assert response.status_code == 422