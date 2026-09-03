import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Repo-root .env for local runs; override so credential updates apply on reload
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)
load_dotenv(override=True)

@dataclass
class Config:
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
    DB_PATH = "users.db"