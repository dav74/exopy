from fastapi import APIRouter, Depends, HTTPException
import logging
from core.security import get_current_user, AuthUser
from core.database import get_db
from models.schemas import RequestExercise
from services.llm import graph
from services.settings import is_ai_configured

router = APIRouter(tags=["llm"])

def _resolve_admin_id(current_user: AuthUser) -> int:
    admin_id = current_user.admin_id
    if not admin_id and current_user.role == "student":
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT admin_id FROM users WHERE username = %s", (current_user.username,))
                row = cur.fetchone()
                if row:
                    admin_id = row[0]
    if not admin_id:
        raise HTTPException(status_code=403, detail="Accès non autorisé.")
    return admin_id

def _check_ai_access(current_user: AuthUser):
    if current_user.role != "student":
        return
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT ai_disabled FROM users WHERE username = %s", (current_user.username,))
            row = cur.fetchone()
            if row and row[0]:
                raise HTTPException(status_code=403, detail="Assistant IA désactivé pour cet élève.")

@router.post('/request')
def request_llm(req: RequestExercise, current_user: AuthUser = Depends(get_current_user)):
    if not is_ai_configured():
        raise HTTPException(status_code=403, detail="Assistant IA non configuré sur le serveur.")

    _check_ai_access(current_user)
    admin_id = _resolve_admin_id(current_user)

    config = {"configurable": {"thread_id": req.session}}
    rep = graph.invoke(
        {
            "enonce": req.enonce,
            "messages": req.code,
            "res_test": req.res_test,
            "is_assistant": req.is_assistant,
            "admin_id": admin_id,
            "user_id": current_user.username,
            "exercise_id": req.exercise_id,
            "session_id": req.session,
            "progress_id": req.progress_id
        },
        config,
        stream_mode="values"
    )
    logging.info(rep['messages'][-1].content)
    return {"response": rep['messages'][-1].content}
