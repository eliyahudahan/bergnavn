# tests/sqlite_fixtures.py
import pytest
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()

class DummyUser(Base):
    __tablename__ = "dummy_users"
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    preferred_sailing_areas = Column(String)  # SQLite-friendly

class RouteTest(Base):
    __tablename__ = "routes"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    legs = relationship("LegTest", back_populates="route")

class LegTest(Base):
    __tablename__ = "legs"
    id = Column(Integer, primary_key=True)
    route_id = Column(Integer, ForeignKey("routes.id"))
    leg_order = Column(Integer)
    route = relationship("RouteTest", back_populates="legs")

@pytest.fixture(scope="session")
def sqlite_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture(scope="function")
def db_session(sqlite_engine):
    Session = sessionmaker(bind=sqlite_engine)
    session = Session()
    yield session
    session.close()
