from fastapi import APIRouter, Depends, HTTPException
import logging
from core.security import get_current_user, AuthUser
from core.database import get_db
from models.schemas import RequestExercise
from services.llm import graph
import psycopg2.extras

router = APIRouter(tags=["llm"])

def _resolve_api_key(current_user: AuthUser) -> tuple[str, int]:
    admin_id = current_user.admin_id
    if not admin_id:
        if current_user.role == "student":
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT admin_id FROM users WHERE username = %s", (current_user.username,))
                    row = cur.fetchone()
                    if not row:
                        raise HTTPException(status_code=403, detail="Aucun administrateur associé.")
                    admin_id = row[0]
        else:
            raise HTTPException(status_code=403, detail="Accès non autorisé.")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT openrouter_api_key FROM admins WHERE id = %s", (admin_id,))
            row = cur.fetchone()
            if not row or not row[0]:
                raise HTTPException(status_code=403, detail="Assistant IA désactivé par l'administrateur.")
            return row[0], admin_id

@router.post('/request')
def request_llm(req: RequestExercise, current_user: AuthUser = Depends(get_current_user)):
    api_key, admin_id = _resolve_api_key(current_user)

    config = {"configurable": {"thread_id": req.session}}
    rep = graph.invoke(
        {
            "enonce": req.enonce,
            "messages": req.code,
            "res_test": req.res_test,
            "is_assistant": req.is_assistant,
            "api_key": api_key,
            "admin_id": admin_id
        }, 
        config, 
        stream_mode="values"
    )
    logging.info(rep['messages'][-1].content)
    return {"response": rep['messages'][-1].content}
