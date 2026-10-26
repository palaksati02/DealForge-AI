import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.base import Base
from app.db.seed import seed_database
from app.db.repositories.procurement_repo import ProcurementRepository

# In-memory SQLite engine with StaticPool so all threads/sessions share the same database
@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture(scope="function")
def db_session(test_engine):
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    seed_database(session)
    yield session
    session.rollback()
    session.close()

@pytest.fixture(scope="function")
def repo(db_session):
    return ProcurementRepository(db_session)

@pytest.fixture(scope="function", autouse=True)
def override_db(db_session):
    from app.db.session import get_db
    from app.main import app
    def _get_db_override():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = _get_db_override
    yield
    app.dependency_overrides.pop(get_db, None)

