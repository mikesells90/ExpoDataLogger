from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "expo.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

DATA_DIR.mkdir(parents=True, exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    from models import Base

    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        cols = conn.execute(text("PRAGMA table_info(booth_entries)")).fetchall()
        col_names = {c[1] for c in cols}
        if "meta_json" not in col_names:
            conn.execute(text("ALTER TABLE booth_entries ADD COLUMN meta_json TEXT"))
