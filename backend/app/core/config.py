import os
from urllib.parse import quote_plus


def _mysql_url_from_env() -> str:
    user = os.getenv("MYSQL_USER", "dicto")
    password = os.getenv("MYSQL_PASSWORD", "dicto_pass")
    name = os.getenv("MYSQL_DATABASE", "dicto")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3306")
    return (
        f"mysql+pymysql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{quote_plus(name)}?charset=utf8mb4"
    )


def build_database_url() -> str:
    """
    Use DATABASE_URL if set (e.g. mysql+pymysql://… for Aiven/Render).

    Otherwise build from MYSQL_* / DB_HOST / DB_PORT (docker-compose).
    """
    explicit = os.getenv("DATABASE_URL")
    if explicit and explicit.strip():
        return explicit.strip()
    return _mysql_url_from_env()


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def _session_samesite() -> str:
    raw = (os.getenv("SESSION_COOKIE_SAMESITE") or "lax").strip().lower()
    if raw == "none":
        return "none"
    if raw == "strict":
        return "strict"
    return "lax"


DATABASE_URL = build_database_url()

API_CORS_ORIGIN = os.getenv("API_CORS_ORIGIN", "http://localhost:5173")

SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "dicto_session")
SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", False)
SESSION_COOKIE_SAMESITE = _session_samesite()

DEFAULT_USER_EMAIL = os.getenv("DEFAULT_USER_EMAIL", "test@dicto.es")
DEFAULT_USER_PASSWORD = os.getenv("DEFAULT_USER_PASSWORD", "uoc123456")
DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@dicto.es")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "uoc123456")


def is_testing() -> bool:
    return bool(os.getenv("TESTING"))
