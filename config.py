"""Environment-based configuration for optional DB/cache."""
import os

REDIS_URL = os.getenv("REDIS_URL", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")

def redis_available() -> bool:
    return bool(REDIS_URL)

def database_available() -> bool:
    return bool(DATABASE_URL)
