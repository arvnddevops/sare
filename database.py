import logging
import traceback
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, Column
from config import LOG_FILE

db = SQLAlchemy()

_logger = logging.getLogger("saree_crm.db")
_handler = logging.FileHandler(LOG_FILE)
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(logging.INFO)

def ensure_columns(app, model_cls):
    """
    Add any missing columns to an SQLite table if they don't exist.
    This is a conservative helper that uses ALTER TABLE ADD COLUMN.
    Call inside app.app_context().
    """
    table_name = model_cls.__tablename__
    mapper = model_cls.__table__
    insp = db.inspect(db.engine)
    if table_name not in insp.get_table_names():
        # Table doesn't exist; create all tables and return
        db.create_all()
        return

    existing_cols = [c["name"] for c in insp.get_columns(table_name)]
    for col in mapper.columns:
        if col.name not in existing_cols:
            try:
                # Only simple ADD COLUMN; SQLite supports basic ALTER TABLE ADD COLUMN
                ddl = f'ALTER TABLE {table_name} ADD COLUMN "{col.name}" {col.type}'
                db.session.execute(ddl)
                db.session.commit()
                _logger.info("Added column %s to %s", col.name, table_name)
            except Exception:
                _logger.error("Error adding column %s to %s:\n%s", col.name, table_name, traceback.format_exc())
