from fastapi import APIRouter, Depends, HTTPException, status
from core.database import get_db
from core.security import get_current_user, get_current_admin
from models.schemas import ExerciseCreate, ExerciseUpdate, ExerciseReorder, ExerciseAIRequest
from services.llm import generate_new_exercise
import logging
import random
import psycopg2.extras

router = APIRouter(tags=["exercises"])

@router.get('/title')
def get_title(current_user: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT exercise_id FROM user_progress WHERE user_id = %s AND status = 'success'",
                    (current_user,)
                )
                success_ids = {row['exercise_id'] for row in cur.fetchall()}

                cur.execute("SELECT id, titre, niveau FROM exercises ORDER BY ordering, id")
                rows = cur.fetchall()

                return {"title": [
                    {
                        "id": row['id'],
                        "title": row['titre'].replace("\n", ""),
                        "niveau": str(row['niveau']),
                        "completed": row['id'] in success_ids
                    } for row in rows
                ]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/admin/exercises/export')
def export_exercises(admin: str = Depends(get_current_admin)):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM exercises ORDER BY ordering, id")
                return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/exercise/{id}')
def get_exercise(id: int, current_user: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM exercises WHERE id = %s", (id,))
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
def ai_generate_exercise(payload: ExerciseAIRequest, admin: str = Depends(get_current_admin)):
    try:
        result = generate_new_exercise(payload.difficulty, payload.existing_titles)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/admin/exercises/reorder')
def reorder_exercises(payload: ExerciseReorder, admin: str = Depends(get_current_admin)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                for index, ex_id in enumerate(payload.ids):
                    cur.execute("UPDATE exercises SET ordering = %s WHERE id = %s", (index, ex_id))
        return {"success": True, "count": len(payload.ids)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/admin/exercise', status_code=status.HTTP_201_CREATED)
def create_exercise(exercise: ExerciseCreate, admin: str = Depends(get_current_admin)):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "INSERT INTO exercises (titre, niveau, enonce, test) VALUES (%s, %s, %s, %s) RETURNING *",
                    (exercise.titre, exercise.niveau, exercise.enonce, exercise.test)
                )
                return dict(cur.fetchone())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put('/admin/exercise/{id}')
def update_exercise(id: int, exercise: ExerciseUpdate, admin: str = Depends(get_current_admin)):
    try:
        update_data = {k: v for k, v in exercise.dict().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No data provided to update")

        fields = ", ".join(f"{k} = %s" for k in update_data)
        values = list(update_data.values()) + [id]

        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    f"UPDATE exercises SET {fields} WHERE id = %s RETURNING *",
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
def delete_exercise(id: int, admin: str = Depends(get_current_admin)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM exercises WHERE id = %s", (id,))
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/admin/exercises/shuffle')
def shuffle_exercises(admin: str = Depends(get_current_admin)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM exercises")
                ids = [row[0] for row in cur.fetchall()]
                random.shuffle(ids)
                for index, ex_id in enumerate(ids):
                    cur.execute("UPDATE exercises SET ordering = %s WHERE id = %s", (index, ex_id))
        return {"success": True, "count": len(ids)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
