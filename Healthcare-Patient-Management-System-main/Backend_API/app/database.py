import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    required = ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"]
    missing = [key for key in required if os.getenv(key) is None]
    if missing:
        raise RuntimeError("Missing database configuration: " + ", ".join(missing))
    try:
        port = int(os.getenv("DB_PORT", "3306"))
    except ValueError:
        raise RuntimeError("DB_PORT must be an integer") from None
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"), port=port, user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"), database=os.getenv("DB_NAME"),
        connection_timeout=10, autocommit=False,
    )
