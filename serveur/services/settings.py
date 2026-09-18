import os
import psycopg2.extras
from core.database import get_db
from core.crypto import decrypt_secret

PROVIDER_CONFIG = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
        "db_key_field": "openrouter_api_key_encrypted",
    },
    "albert": {
        "base_url": "https://albert.api.etalab.gouv.fr/v1",
        "api_key_env": "ALBERT_API_KEY",
        "db_key_field": "albert_api_key_encrypted",
    },
}

# "auto" : mode privilégiant Albert avec repli automatique vers OpenRouter
# (voir services/llm_fallback.py) ; ce n'est pas un fournisseur réel, donc il
# n'a pas d'entrée dans PROVIDER_CONFIG.
LLM_PROVIDER_MODES = {"openrouter", "albert", "auto"}

DEFAULT_LLM_SETTINGS = {
    "llm_provider": "openrouter",
    "llm_model_openrouter": "deepseek/deepseek-v4-flash",
    "llm_model_albert": "deepseek-v4-flash",
    "openrouter_api_key_encrypted": None,
    "albert_api_key_encrypted": None,
}

def get_llm_settings() -> dict:
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """SELECT llm_provider, llm_model_openrouter, llm_model_albert,
                              openrouter_api_key_encrypted, albert_api_key_encrypted
                       FROM app_settings WHERE id = 1"""
                )
                row = cur.fetchone()
                if row:
                    return dict(row)
    except Exception:
        pass
    return dict(DEFAULT_LLM_SETTINGS)

def resolve_api_key(provider: str, settings: dict) -> str | None:
    """Clé DB (déchiffrée) si enregistrée, sinon variable d'environnement."""
    cfg = PROVIDER_CONFIG.get(provider, PROVIDER_CONFIG["openrouter"])
    encrypted = settings.get(cfg["db_key_field"])
    if encrypted:
        decrypted = decrypt_secret(encrypted)
        if decrypted:
            return decrypted
    return os.getenv(cfg["api_key_env"])

def get_active_provider_api_key(settings: dict | None = None) -> str | None:
    settings = settings or get_llm_settings()
    provider = settings.get("llm_provider", "openrouter")
    if provider == "auto":
        return resolve_api_key("albert", settings) or resolve_api_key("openrouter", settings)
    return resolve_api_key(provider, settings)

def is_ai_configured() -> bool:
    return bool(get_active_provider_api_key())

def _mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 4:
        return "*" * len(key)
    return f"{key[:3]}...{key[-4:]}"

def describe_provider_key(provider: str, settings: dict) -> dict:
    """Renseigne si une clé est disponible pour ce fournisseur, sa provenance
    (base ou variable d'environnement) et un indice masqué, sans jamais
    exposer la clé en clair."""
    cfg = PROVIDER_CONFIG[provider]
    encrypted = settings.get(cfg["db_key_field"])
    if encrypted:
        decrypted = decrypt_secret(encrypted)
        if decrypted:
            return {"configured": True, "source": "database", "hint": _mask_key(decrypted)}
    env_key = os.getenv(cfg["api_key_env"])
    if env_key:
        return {"configured": True, "source": "environment", "hint": _mask_key(env_key)}
    return {"configured": False, "source": None, "hint": None}
