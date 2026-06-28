from pathlib import Path

from .database import Database
from .save_repository import SaveRepository

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "db"

DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "factory_lab.db"

database = Database(DB_PATH)
save_repository = SaveRepository(database)

__all__ = [
    "Database",
    "SaveRepository",
    "database",
    "save_repository",
]