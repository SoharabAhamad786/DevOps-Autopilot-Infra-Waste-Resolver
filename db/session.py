from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from contextlib import contextmanager
from config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    echo=False
)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()

def init_db():
    import db.models  # Ensure models are registered with Base
    Base.metadata.create_all(bind=engine)

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
        SessionLocal.remove()
