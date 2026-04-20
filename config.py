import os

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be set in .env or environment")

ALGORITHM = os.getenv("ALGORITHM", "HS256")
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "5"))
ACCESS_TOKEN_EXPIRE_SECONDS = int(os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS", "3600"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tasks.db")
LOG_FILE = os.getenv("LOG_FILE", "app.log")
USER_CREDENTIALS = os.getenv("USER_CREDENTIALS", "alice:alice123,bob:bobPassword")
