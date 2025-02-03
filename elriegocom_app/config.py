import os
from dataclasses import dataclass

@dataclass
class Config:
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
    DB_PATH = "users.db"