import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = os.environ.get("SAREE_DB", str(BASE_DIR / "saree.db"))
LOG_FILE = os.environ.get("SAREE_LOG", str(BASE_DIR / "crm.log"))
DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret")
SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"
SQLALCHEMY_TRACK_MODIFICATIONS = False
