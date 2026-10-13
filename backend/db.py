from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

# Connection poolers such as Supabase's (port 6543) give each transaction a different server connection,
# which breaks psycopg's prepared statements after a few repeats of the same query. Turn them off.
_connect_args = {"prepare_threshold": None} if settings.database_url.startswith("postgresql+psycopg") else {}
engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    with SessionLocal() as db:
        yield db
