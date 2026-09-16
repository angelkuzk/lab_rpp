import os
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError

load_dotenv()

app = Flask(__name__)

# Строка подключения собирается из переменных окружения
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# Модель Visit: id (PK), время обращения, IP-адрес клиента
class Visit(db.Model):
    __tablename__ = "visits"

    id = db.Column(db.Integer, primary_key=True)
    visited_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    ip_address = db.Column(db.String(45), nullable=False)


# Создание таблицы visits при старте приложения 
def init_db(retries: int = 15, delay: float = 2.0) -> None:
    for attempt in range(1, retries + 1):
        try:
            with app.app_context():
                db.create_all()
            print("[init_db] tables created")
            return
        except OperationalError as e:
            print(f"[init_db] DB not ready ({attempt}/{retries}): {e}")
            time.sleep(delay)
    raise RuntimeError("Database is not available")


init_db()


# GET /hello
@app.route("/hello", methods=["GET"])
def hello():
    visited_at = datetime.now(timezone.utc)
    ip_address = request.remote_addr

    visit = Visit(visited_at=visited_at, ip_address=ip_address)
    db.session.add(visit)
    db.session.commit()

    return "Hello", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)