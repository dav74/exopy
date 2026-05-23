from fastapi import APIRouter, Depends, HTTPException, status
from core.database import get_db
from core.security import get_current_user, get_current_admin, AuthUser
from models.schemas import ExerciseCreate, ExerciseUpdate, ExerciseReorder, ExerciseAIRequest
from services.llm import generate_new_exercise
import logging
import random
import psycopg2.extras

router = APIRouter(tags=["exercises"])

def _get_admin_id_for_user(user: AuthUser) -> int:
    if user.admin_id:
        return user.admin_id
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT admin_id FROM users WHERE username = %s", (user.username,))
                row = cur.fetchone()
                if row:
                    return row[0]
    except Exception:
        pass
    return None

def _get_admin_api_key(admin_id: int) -> str | None:
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT openrouter_api_key FROM admins WHERE id = %s", (admin_id,))
                row = cur.fetchone()
                return row[0] if row else None
    except Exception:
        return None

@router.get('/title')
def get_title(current_user: AuthUser = Depends(get_current_user)):
    admin_id = _get_admin_id_for_user(current_user)
    if not admin_id:
        raise HTTPException(status_code=403, detail="Aucun administrateur associé.")

    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT exercise_id FROM user_progress WHERE user_id = %s AND status = 'success'",
                    (current_user.username,)
                )
                success_ids = {row['exercise_id'] for row in cur.fetchall()}

                cur.execute(
                    "SELECT id, titre, niveau FROM exercises WHERE admin_id = %s ORDER BY ordering, id",
                    (admin_id,)
                )
                rows = cur.fetchall()

                return {"title": [
                    {
                        "id": row['id'],
                        "title": row['titre'].replace("\n", ""),
                        "niveau": str(row['niveau']),
                        "completed": row['id'] in success_ids
                    } for row in rows
                ]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/admin/exercises/export')
def export_exercises(admin: AuthUser = Depends(get_current_admin)):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM exercises WHERE admin_id = %s ORDER BY ordering, id",
                    (admin.admin_id,)
                )
                return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/exercise/{id}')
def get_exercise(id: int, current_user: AuthUser = Depends(get_current_user)):
    admin_id = _get_admin_id_for_user(current_user)
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM exercises WHERE id = %s AND admin_id = %s",
                    (id, admin_id)
                )
                ex = cur.fetchone()
                if not ex:
                    raise HTTPException(status_code=404, detail="Exercise not found")
                logging.info(f"Endpoint /exercise/{id} called")
                return {
                    "id": id,
                    "title": ex['titre'].replace("\n", ""),
                    "niveau": str(ex['niveau']),
                    "enonce": ex['enonce'],
                    "test": ex['test']
                }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/admin/exercises/generate')
def ai_generate_exercise(payload: ExerciseAIRequest, admin: AuthUser = Depends(get_current_admin)):
    try:
        api_key = _get_admin_api_key(admin.admin_id)
        if not api_key:
            raise HTTPException(status_code=403, detail="Clé API OpenRouter non configurée. Ajoutez votre clé dans l'onglet 'Mon compte'.")
        result = generate_new_exercise(payload.difficulty, payload.existing_titles, api_key)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/admin/exercises/reorder')
def reorder_exercises(payload: ExerciseReorder, admin: AuthUser = Depends(get_current_admin)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                for index, ex_id in enumerate(payload.ids):
                    cur.execute(
                        "UPDATE exercises SET ordering = %s WHERE id = %s AND admin_id = %s",
                        (index, ex_id, admin.admin_id)
                    )
        return {"success": True, "count": len(payload.ids)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/admin/exercise', status_code=status.HTTP_201_CREATED)
def create_exercise(exercise: ExerciseCreate, admin: AuthUser = Depends(get_current_admin)):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "INSERT INTO exercises (titre, niveau, enonce, test, admin_id) VALUES (%s, %s, %s, %s, %s) RETURNING *",
                    (exercise.titre, exercise.niveau, exercise.enonce, exercise.test, admin.admin_id)
                )
                return dict(cur.fetchone())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put('/admin/exercise/{id}')
def update_exercise(id: int, exercise: ExerciseUpdate, admin: AuthUser = Depends(get_current_admin)):
    try:
        update_data = {k: v for k, v in exercise.dict().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No data provided to update")

        fields = ", ".join(f"{k} = %s" for k in update_data)
        values = list(update_data.values()) + [id, admin.admin_id]

        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    f"UPDATE exercises SET {fields} WHERE id = %s AND admin_id = %s RETURNING *",
                    values
                )
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Exercise not found")
                return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete('/admin/exercise/{id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(id: int, admin: AuthUser = Depends(get_current_admin)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM exercises WHERE id = %s AND admin_id = %s",
                    (id, admin.admin_id)
                )
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/admin/exercises/shuffle')
def shuffle_exercises(admin: AuthUser = Depends(get_current_admin)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM exercises WHERE admin_id = %s", (admin.admin_id,))
                ids = [row[0] for row in cur.fetchall()]
                random.shuffle(ids)
                for index, ex_id in enumerate(ids):
                    cur.execute(
                        "UPDATE exercises SET ordering = %s WHERE id = %s AND admin_id = %s",
                        (index, ex_id, admin.admin_id)
                    )
        return {"success": True, "count": len(ids)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
