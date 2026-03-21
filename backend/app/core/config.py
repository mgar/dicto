import os

DB_USER = os.getenv("MYSQL_USER", "dicto")
DB_PASS = os.getenv("MYSQL_PASSWORD", "dicto_pass")
DB_NAME = os.getenv("MYSQL_DATABASE", "dicto")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)

API_CORS_ORIGIN = os.getenv("API_CORS_ORIGIN", "http://localhost:5173")

SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "dicto_session")

DEFAULT_USER_EMAIL = os.getenv("DEFAULT_USER_EMAIL", "test@dicto.es")
DEFAULT_USER_PASSWORD = os.getenv("DEFAULT_USER_PASSWORD", "changeme")
DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@dicto.es")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "changeme")


def is_testing() -> bool:
    return bool(os.getenv("TESTING"))
