import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory paths
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

# Load environment variables safely with utf-8 handling
for env_path in [BASE_DIR / ".env", ROOT_DIR / ".env"]:
    if env_path.exists():
        try:
            load_dotenv(env_path, encoding="utf-8")
        except Exception:
            try:
                load_dotenv(env_path, encoding="utf-16")
            except Exception:
                pass

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "podcastgpt-dev-secret-key-2026")
    ENVIRONMENT = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
    PORT = int(os.getenv("PORT", 5000))
    HOST = os.getenv("HOST", "127.0.0.1")

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

    # SQLite Persistent Storage
    DATA_DIR = BASE_DIR / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "podcastgpt.db"))

    # Vector Store (ChromaDB)
    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(DATA_DIR / "chroma"))

    # AI & LLM Providers
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    DEFAULT_LLM_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "gemini")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")

    # Search Limits
    MAX_SEARCH_RESULTS = 25
    REQUEST_TIMEOUT = 10 # seconds

config = Config()
