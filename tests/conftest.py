import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import app.db.session
import app.mcp.tools.procurement_tools as pt
from app.db.base import Base
from app.db.seed import seed_database
from app.db.repositories.procurement_repo import ProcurementRepository

# In-memory SQLite engine with StaticPool for cross-session test isolation
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture(scope="function")
def db_session(test_engine, monkeypatch):
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    monkeypatch.setattr(app.db.session, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(pt, "SessionLocal", TestingSessionLocal)
    session = TestingSessionLocal()
    seed_database(session)
    yield session
    session.rollback()
    session.close()

@pytest.fixture(scope="function")
def repo(db_session):
    return ProcurementRepository(db_session)

@pytest.fixture(scope="function")
def client():
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)
