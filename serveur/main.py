from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

from routers import auth, exercises, llm, metrics, admin_mgmt
from core.database import get_db
from passlib.hash import bcrypt
import psycopg2.extras

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="EXOPY API", description="API for learning Python with GenAI assistance")

_origins_env = os.getenv("CORS_ORIGINS", "")
if _origins_env:
    origins = [o.strip() for o in _origins_env.split(",") if o.strip()]
else:
    origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(exercises.router)
app.include_router(llm.router)
app.include_router(metrics.router)
app.include_router(admin_mgmt.router)

@app.on_event("startup")
def startup():
    _migrate()
    _bootstrap_superadmin()

def _migrate():
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'admins')")
                if cur.fetchone()[0]:
                    return

                cur.execute("""
                    CREATE TABLE admins (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(255) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        openrouter_api_key VARCHAR(512) DEFAULT NULL,
                        is_super BOOLEAN DEFAULT FALSE
                    )
                """)

                cur.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'admin_id')")
                if not cur.fetchone()[0]:
                    cur.execute("ALTER TABLE users ADD COLUMN admin_id INTEGER REFERENCES admins(id) ON DELETE CASCADE")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_users_admin_id ON users(admin_id)")

                cur.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'exercises' AND column_name = 'admin_id')")
                if not cur.fetchone()[0]:
                    cur.execute("ALTER TABLE exercises ADD COLUMN admin_id INTEGER REFERENCES admins(id) ON DELETE CASCADE")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_exercises_admin_id ON exercises(admin_id)")

                logging.info("Database migration: admins table and admin_id columns created.")
    except Exception as e:
        logging.error(f"Migration error: {e}")

def _bootstrap_superadmin():
    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_username or not admin_password:
        logging.warning("ADMIN_USERNAME or ADMIN_PASSWORD not set. Super-admin bootstrap skipped.")
        return

    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT id, password_hash FROM admins WHERE username = %s AND is_super = TRUE", (admin_username,))
                row = cur.fetchone()

                if row:
                    super_admin_id = row['id']
                    if not bcrypt.verify(admin_password, row['password_hash']):
                        cur.execute(
                            "UPDATE admins SET password_hash = %s WHERE id = %s",
                            (bcrypt.using(rounds=6).hash(admin_password), super_admin_id)
                        )
                        logging.info("Super-admin password updated from environment variables.")
                else:
                    cur.execute(
                        "INSERT INTO admins (username, password_hash, is_super) VALUES (%s, %s, TRUE) RETURNING id",
                        (admin_username, bcrypt.using(rounds=6).hash(admin_password))
                    )
                    super_admin_id = cur.fetchone()['id']
                    logging.info(f"Super-admin '{admin_username}' created (id={super_admin_id}).")

                cur.execute("UPDATE users SET admin_id = %s WHERE admin_id IS NULL", (super_admin_id,))
                cur.execute("UPDATE exercises SET admin_id = %s WHERE admin_id IS NULL", (super_admin_id,))
    except Exception as e:
        logging.error(f"Super-admin bootstrap error: {e}")

@app.get("/")
def read_root():
    return {"message": "Welcome to EXOPY API"}
