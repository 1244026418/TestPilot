from pathlib import Path
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _build_database_url() -> str:
    explicit_url = os.getenv("TESTPILOT_DATABASE_URL", "").strip()
    if explicit_url:
        return explicit_url

    driver = os.getenv("TESTPILOT_DB_DRIVER", "mysql").strip().lower()
    if driver == "sqlite":
        return f"sqlite:///{BASE_DIR / 'testpilot.db'}"

    host = os.getenv("TESTPILOT_MYSQL_HOST", "127.0.0.1")
    port = os.getenv("TESTPILOT_MYSQL_PORT", "3306")
    user = os.getenv("TESTPILOT_MYSQL_USER", "root")
    password = quote_plus(os.getenv("TESTPILOT_MYSQL_PASSWORD", ""))
    database = os.getenv("TESTPILOT_MYSQL_DATABASE", "testpilot")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"


DATABASE_URL = _build_database_url()
SECRET_KEY = os.getenv("TESTPILOT_SECRET_KEY", "dev-secret-key")
TOKEN_EXPIRE_HOURS = int(os.getenv("TESTPILOT_TOKEN_EXPIRE_HOURS", "24"))
REPORT_DIR = Path(os.getenv("TESTPILOT_REPORT_DIR", str(BASE_DIR / "reports"))).resolve()
REPORT_DIR.mkdir(parents=True, exist_ok=True)
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
