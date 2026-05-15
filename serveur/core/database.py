import os
import psycopg2
import psycopg2.pool
import psycopg2.extras
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL doit être défini dans le fichier .env")

_pool = psycopg2.pool.ThreadedConnectionPool(1, 10, DATABASE_URL)

@contextmanager
def get_db():
    conn = _pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)
