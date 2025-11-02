from flask import Flask
import logging, traceback
from config import LOG_FILE, DEBUG, SECRET_KEY, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
from database import db, ensure_columns
import models  # ensure models seen by SQLAlchemy
from routes import bp as main_bp
from models import Customer, Order, Payment, FollowUp

def create_app():
    app = Flask(__name__)
    app.config.from_object("config")
    # Set up database
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = SQLALCHEMY_TRACK_MODIFICATIONS
    app.secret_key = SECRET_KEY

    # Logging
    handler = logging.FileHandler(LOG_FILE)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    db.init_app(app)

    # Blueprints
    app.register_blueprint(main_bp)

    # Safe schema ensure
    with app.app_context():
        try:
            # Create tables if not exists
            db.create_all()
            # Extra: ensure columns for each model (lightweight migrations)
            ensure_columns(app, Customer)
            ensure_columns(app, Order)
            ensure_columns(app, Payment)
            ensure_columns(app, FollowUp)
        except Exception:
            app.logger.error("Schema init failed:\n%s", traceback.format_exc())

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=DEBUG)
