import pytest
from typing import Generator
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal

@pytest.fixture(scope="module")
def db() -> Generator:
    yield SessionLocal()

@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c
