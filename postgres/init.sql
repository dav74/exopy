-- Schéma de base de données Exopy
-- Ce fichier est exécuté automatiquement au premier démarrage du conteneur PostgreSQL

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nom VARCHAR(255) NOT NULL DEFAULT '',
    prenom VARCHAR(255) NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS exercises (
    id SERIAL PRIMARY KEY,
    titre TEXT NOT NULL,
    niveau INTEGER NOT NULL DEFAULT 1,
    enonce TEXT NOT NULL,
    test TEXT NOT NULL,
    mots_cle TEXT NOT NULL DEFAULT '',
    ordering INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS user_progress (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    exercise_id INTEGER NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    error_type VARCHAR(255),
    session_id VARCHAR(255),
    duration INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_progress_user_id ON user_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_progress_exercise_id ON user_progress(exercise_id);
CREATE INDEX IF NOT EXISTS idx_exercises_ordering ON exercises(ordering);
