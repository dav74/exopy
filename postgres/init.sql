-- Schéma de base de données Exopy
-- Ce fichier est exécuté automatiquement au premier démarrage du conteneur PostgreSQL

CREATE TABLE IF NOT EXISTS admins (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nom VARCHAR(255) NOT NULL DEFAULT '',
    prenom VARCHAR(255) NOT NULL DEFAULT '',
    etablissement VARCHAR(255) DEFAULT NULL,
    email VARCHAR(255) DEFAULT NULL,
    openrouter_api_key VARCHAR(512) DEFAULT NULL,
    is_super BOOLEAN DEFAULT FALSE,
    must_change_password BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nom VARCHAR(255) NOT NULL DEFAULT '',
    prenom VARCHAR(255) NOT NULL DEFAULT '',
    admin_id INTEGER NOT NULL REFERENCES admins(id) ON DELETE CASCADE,
    must_change_password BOOLEAN NOT NULL DEFAULT FALSE,
    ai_disabled BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS exercises (
    id SERIAL PRIMARY KEY,
    titre TEXT NOT NULL,
    niveau INTEGER NOT NULL DEFAULT 1,
    enonce TEXT NOT NULL,
    test TEXT NOT NULL,
    mots_cle TEXT NOT NULL DEFAULT '',
    ordering INTEGER NOT NULL DEFAULT 0,
    admin_id INTEGER NOT NULL REFERENCES admins(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_progress (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    exercise_id INTEGER NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    error_type VARCHAR(255),
    session_id VARCHAR(255),
    duration INTEGER,
    code TEXT,
    ai_used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Persiste chaque échange élève <-> assistant IA (le checkpointer LangGraph
-- ne conserve l'historique qu'en mémoire process, perdu au redémarrage).
CREATE TABLE IF NOT EXISTS ai_interactions (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    exercise_id INTEGER REFERENCES exercises(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    interaction_type VARCHAR(20) NOT NULL,
    student_code TEXT,
    ai_response TEXT NOT NULL,
    model VARCHAR(255),
    -- Lien exact et non ambigu vers la tentative de soumission qui a déclenché
    -- cet appel, transmis explicitement par le client (et non déduit après coup
    -- par corrélation temporelle, qui serait sujette à erreur si l'appel LLM est
    -- lent et que l'élève resoumet du code entre-temps).
    progress_id INTEGER REFERENCES user_progress(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Pseudonymisation stable pour les exports destinés à la recherche : le
-- pseudo_id est généré une seule fois et jamais recalculé, afin de permettre
-- un suivi longitudinal du même élève sans jamais exposer son identité réelle
-- au chercheur. Cette table ne quitte jamais la base de production.
CREATE TABLE IF NOT EXISTS research_pseudonyms (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL REFERENCES users(username) ON DELETE CASCADE,
    pseudo_id VARCHAR(64) UNIQUE NOT NULL,
    admin_id INTEGER NOT NULL REFERENCES admins(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enregistre le résultat d'un consentement obtenu hors-application (formulaire
-- papier signé par l'élève/les parents/l'établissement) ; ne collecte pas le
-- consentement lui-même. consent_given = FALSE ou revoked_at renseigné exclut
-- l'élève de tout export de recherche.
CREATE TABLE IF NOT EXISTS research_consent (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL REFERENCES users(username) ON DELETE CASCADE,
    consent_given BOOLEAN NOT NULL DEFAULT FALSE,
    recorded_by VARCHAR(255),
    consented_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE
);

-- Configuration globale de l'assistant IA (un seul fournisseur actif pour
-- toute l'application, modifiable par le super-admin sans redémarrage).
-- Table singleton : une seule ligne, id = 1, jamais d'autre ligne insérée.
-- Les clés API des fournisseurs IA peuvent être enregistrées ici (chiffrées avec
-- SECRET_KEY, jamais en clair) depuis le panel super-admin, en plus des variables
-- d'environnement OPENROUTER_API_KEY / ALBERT_API_KEY qui servent de repli.
CREATE TABLE IF NOT EXISTS app_settings (
    id INTEGER PRIMARY KEY DEFAULT 1,
    llm_provider VARCHAR(20) NOT NULL DEFAULT 'openrouter',
    llm_model_openrouter VARCHAR(255) NOT NULL DEFAULT 'deepseek/deepseek-v4-flash',
    llm_model_albert VARCHAR(255) NOT NULL DEFAULT 'deepseek-v4-flash',
    openrouter_api_key_encrypted TEXT DEFAULT NULL,
    albert_api_key_encrypted TEXT DEFAULT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO app_settings (id) VALUES (1) ON CONFLICT (id) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_research_pseudonyms_admin_id ON research_pseudonyms(admin_id);

CREATE INDEX IF NOT EXISTS idx_user_progress_user_id ON user_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_progress_exercise_id ON user_progress(exercise_id);
CREATE INDEX IF NOT EXISTS idx_exercises_ordering ON exercises(ordering);
CREATE INDEX IF NOT EXISTS idx_users_admin_id ON users(admin_id);
CREATE INDEX IF NOT EXISTS idx_exercises_admin_id ON exercises(admin_id);
CREATE INDEX IF NOT EXISTS idx_ai_interactions_user_id ON ai_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_interactions_exercise_id ON ai_interactions(exercise_id);
CREATE INDEX IF NOT EXISTS idx_ai_interactions_session_id ON ai_interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_interactions_progress_id ON ai_interactions(progress_id);
