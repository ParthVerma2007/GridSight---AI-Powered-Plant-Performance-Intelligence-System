import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.ingestion.pipeline import IngestionPipeline

TEST_DATABASE_URL = "sqlite:///./test_plant.db"

@pytest.fixture(scope="session")
def engine():
    test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("./test_plant.db"):
        try:
            os.remove("./test_plant.db")
        except Exception:
            pass

@pytest.fixture(scope="function")
def db(engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    pipeline = IngestionPipeline(session)
    pipeline.ensure_default_plant_and_assets("helios-50")
    yield session
    session.rollback()
    session.close()
