from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = BASE_DIR / "data"
DB_DIR = DATA_DIR / "db"
CAPTURES_DIR = DATA_DIR / "captures"

ASSETS_DIR = BASE_DIR / "assets"

APP_NAME = "Jewelry SW"
APP_VERSION = "2.0"
