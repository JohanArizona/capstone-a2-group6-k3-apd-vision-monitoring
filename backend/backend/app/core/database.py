import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Ambil DATABASE_URL dari environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://capstone_user:capstone_password@localhost:5432/capstone_db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using them
    echo=False  # Set True untuk debug SQL queries
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class untuk models
Base = declarative_base()

def get_db():
    """Dependency untuk FastAPI yang menyediakan database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
