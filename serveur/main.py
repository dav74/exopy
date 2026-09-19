from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

from routers import auth, exercises, llm, metrics, admin_mgmt, research
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
app.include_router(research.router)

@app.on_event("startup")
def startup():
    _migrate()
    _bootstrap_superadmin()

def _migrate():
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'admins')")
                if not cur.fetchone()[0]:
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

                cur.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'must_change_password')")
                if not cur.fetchone()[0]:
                    cur.execute("ALTER TABLE users ADD COLUMN must_change_password BOOLEAN NOT NULL DEFAULT FALSE")
                    logging.info("Database migration: must_change_password column added to users.")

                cur.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'admins' AND column_name = 'must_change_password')")
                if not cur.fetchone()[0]:
                    cur.execute("ALTER TABLE admins ADD COLUMN must_change_password BOOLEAN NOT NULL DEFAULT FALSE")
                    logging.info("Database migration: must_change_password column added to admins.")

                cur.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'admins' AND column_name = 'nom')")
                if not cur.fetchone()[0]:
                    cur.execute("ALTER TABLE admins ADD COLUMN nom VARCHAR(255) NOT NULL DEFAULT ''")
                    cur.execute("ALTER TABLE admins ADD COLUMN prenom VARCHAR(255) NOT NULL DEFAULT ''")
                    cur.execute("ALTER TABLE admins ADD COLUMN etablissement VARCHAR(255) DEFAULT NULL")
                    cur.execute("ALTER TABLE admins ADD COLUMN email VARCHAR(255) DEFAULT NULL")
                    logging.info("Database migration: nom/prenom/etablissement/email columns added to admins.")

                cur.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'ai_disabled')")
                if not cur.fetchone()[0]:
                    cur.execute("ALTER TABLE users ADD COLUMN ai_disabled BOOLEAN NOT NULL DEFAULT FALSE")
                    logging.info("Database migration: ai_disabled column added to users.")

                cur.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'admins' AND column_name = 'ai_disabled')")
                if not cur.fetchone()[0]:
                    cur.execute("ALTER TABLE admins ADD COLUMN ai_disabled BOOLEAN NOT NULL DEFAULT FALSE")
                    logging.info("Database migration: ai_disabled column added to admins.")

                cur.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'admins' AND column_name = 'ai_locked_by_super')")
                if not cur.fetchone()[0]:
                    cur.execute("ALTER TABLE admins ADD COLUMN ai_locked_by_super BOOLEAN NOT NULL DEFAULT FALSE")
                    logging.info("Database migration: ai_locked_by_super column added to admins.")

                cur.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'niveau')")
                if not cur.fetchone()[0]:
                    cur.execute("ALTER TABLE users ADD COLUMN niveau VARCHAR(1) NOT NULL DEFAULT ''")
                    cur.execute("ALTER TABLE users ADD CONSTRAINT users_niveau_check CHECK (niveau IN ('', 'T', 'P'))")
                    logging.info("Database migration: niveau column added to users.")

                cur.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'user_progress' AND column_name = 'code')")
                if not cur.fetchone()[0]:
                    cur.execute("ALTER TABLE user_progress ADD COLUMN code TEXT")
                    logging.info("Database migration: code column added to user_progress.")

                cur.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'user_progress' AND column_name = 'ai_used')")
                if not cur.fetchone()[0]:
                    cur.execute("ALTER TABLE user_progress ADD COLUMN ai_used BOOLEAN NOT NULL DEFAULT FALSE")
                    logging.info("Database migration: ai_used column added to user_progress.")

                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ai_interactions')")
                if not cur.fetchone()[0]:
                    cur.execute("""
                        CREATE TABLE ai_interactions (
                            id BIGSERIAL PRIMARY KEY,
                            user_id VARCHAR(255) NOT NULL,
                            exercise_id INTEGER REFERENCES exercises(id) ON DELETE CASCADE,
                            session_id VARCHAR(255) NOT NULL,
                            interaction_type VARCHAR(20) NOT NULL,
                            student_code TEXT,
                            ai_response TEXT NOT NULL,
                            model VARCHAR(255),
                            progress_id INTEGER REFERENCES user_progress(id) ON DELETE SET NULL,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        )
                    """)
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_ai_interactions_user_id ON ai_interactions(user_id)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_ai_interactions_exercise_id ON ai_interactions(exercise_id)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_ai_interactions_session_id ON ai_interactions(session_id)")
                    logging.info("Database migration: ai_interactions table created.")

                cur.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'ai_interactions' AND column_name = 'progress_id')")
                if not cur.fetchone()[0]:
                    cur.execute("ALTER TABLE ai_interactions ADD COLUMN progress_id INTEGER REFERENCES user_progress(id) ON DELETE SET NULL")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_ai_interactions_progress_id ON ai_interactions(progress_id)")
                    logging.info("Database migration: progress_id column added to ai_interactions.")

                # Rattache rétroactivement les interactions IA historiques (créées avant
                # l'introduction de progress_id, ou lors d'un précédent démarrage où la colonne
                # existait déjà) à leur tentative user_progress : même utilisateur/exercice/session,
                # la tentative success/failure la plus récente précédant l'interaction (elle est
                # toujours journalisée avant l'appel à l'assistant côté client). N'écrase jamais un
                # lien déjà posé par le client, ne devine rien quand aucune correspondance n'existe
                # (progress_id reste NULL). Hors du bloc ci-dessus car idempotent (ne touche que les
                # lignes encore NULL) : peut se rejouer sans risque à chaque démarrage.
                cur.execute("""
                    UPDATE ai_interactions ai
                    SET progress_id = matched.progress_id
                    FROM (
                        SELECT DISTINCT ON (ai2.id) ai2.id AS interaction_id, up.id AS progress_id
                        FROM ai_interactions ai2
                        JOIN user_progress up
                          ON up.user_id = ai2.user_id
                         AND up.exercise_id = ai2.exercise_id
                         AND up.session_id = ai2.session_id
                         AND up.status IN ('success', 'failure')
                         AND up.created_at <= ai2.created_at
                        WHERE ai2.progress_id IS NULL
                        ORDER BY ai2.id, up.created_at DESC
                    ) matched
                    WHERE ai.id = matched.interaction_id
                """)
                if cur.rowcount:
                    logging.info(f"Database migration: backfilled progress_id for {cur.rowcount} historical ai_interactions rows.")

                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'research_pseudonyms')")
                if not cur.fetchone()[0]:
                    cur.execute("""
                        CREATE TABLE research_pseudonyms (
                            id SERIAL PRIMARY KEY,
                            user_id VARCHAR(255) UNIQUE NOT NULL REFERENCES users(username) ON DELETE CASCADE,
                            pseudo_id VARCHAR(64) UNIQUE NOT NULL,
                            admin_id INTEGER NOT NULL REFERENCES admins(id) ON DELETE CASCADE,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        )
                    """)
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_research_pseudonyms_admin_id ON research_pseudonyms(admin_id)")
                    logging.info("Database migration: research_pseudonyms table created.")

                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'research_consent')")
                if not cur.fetchone()[0]:
                    cur.execute("""
                        CREATE TABLE research_consent (
                            id SERIAL PRIMARY KEY,
                            user_id VARCHAR(255) UNIQUE NOT NULL REFERENCES users(username) ON DELETE CASCADE,
                            consent_given BOOLEAN NOT NULL DEFAULT FALSE,
                            recorded_by VARCHAR(255),
                            consented_at TIMESTAMP WITH TIME ZONE,
                            revoked_at TIMESTAMP WITH TIME ZONE
                        )
                    """)
                    logging.info("Database migration: research_consent table created.")

                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'app_settings')")
                if not cur.fetchone()[0]:
                    cur.execute("""
                        CREATE TABLE app_settings (
                            id INTEGER PRIMARY KEY DEFAULT 1,
                            llm_provider VARCHAR(20) NOT NULL DEFAULT 'openrouter',
                            llm_model_openrouter VARCHAR(255) NOT NULL DEFAULT 'deepseek/deepseek-v4-flash',
                            llm_model_albert VARCHAR(255) NOT NULL DEFAULT 'deepseek-v4-flash',
                            openrouter_api_key_encrypted TEXT DEFAULT NULL,
                            albert_api_key_encrypted TEXT DEFAULT NULL,
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        )
                    """)
                    cur.execute("INSERT INTO app_settings (id) VALUES (1) ON CONFLICT (id) DO NOTHING")
                    logging.info("Database migration: app_settings table created.")

                cur.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'app_settings' AND column_name = 'openrouter_api_key_encrypted')")
                if not cur.fetchone()[0]:
                    cur.execute("ALTER TABLE app_settings ADD COLUMN openrouter_api_key_encrypted TEXT DEFAULT NULL")
                    cur.execute("ALTER TABLE app_settings ADD COLUMN albert_api_key_encrypted TEXT DEFAULT NULL")
                    logging.info("Database migration: encrypted API key columns added to app_settings.")
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
                            (bcrypt.using(rounds=12).hash(admin_password), super_admin_id)
                        )
                        logging.info("Super-admin password updated from environment variables.")
                else:
                    cur.execute(
                        "INSERT INTO admins (username, password_hash, is_super) VALUES (%s, %s, TRUE) RETURNING id",
                        (admin_username, bcrypt.using(rounds=12).hash(admin_password))
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
