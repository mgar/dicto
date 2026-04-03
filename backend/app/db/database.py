import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import DATABASE_URL

_connect_args = {}
if DATABASE_URL.startswith("mysql") and os.getenv("MYSQL_SSL_REQUIRE", "").strip().lower() in (
    "1",
    "true",
    "yes",
    "on",
):
    # Managed MySQL (for deployment with Render/Aiven)
    _connect_args["ssl"] = {}

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass
