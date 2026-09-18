import threading
import time

# Circuit breaker en mémoire (process unique) pour le mode "auto" :
# priorité à Albert, repli sur OpenRouter tant qu'Albert échoue, avec une
# tentative de reprise (half-open) après un délai de cooldown.

ALBERT_COOLDOWN_SECONDS = 15

_lock = threading.Lock()
_state = {"open": False, "opened_at": 0.0}


def is_albert_circuit_open() -> bool:
    """True si Albert doit être évité pour le prochain appel en mode auto."""
    with _lock:
        if not _state["open"]:
            return False
        if time.monotonic() - _state["opened_at"] >= ALBERT_COOLDOWN_SECONDS:
            # Cooldown écoulé : on autorise une tentative de reprise (half-open).
            return False
        return True


def record_albert_failure() -> None:
    with _lock:
        _state["open"] = True
        _state["opened_at"] = time.monotonic()


def record_albert_success() -> None:
    with _lock:
        _state["open"] = False
        _state["opened_at"] = 0.0


def get_status() -> dict:
    with _lock:
        if not _state["open"]:
            return {"open": False, "since": None, "next_retry_in": 0}
        elapsed = time.monotonic() - _state["opened_at"]
        return {
            "open": True,
            "since": _state["opened_at"],
            "next_retry_in": max(0.0, ALBERT_COOLDOWN_SECONDS - elapsed),
        }
