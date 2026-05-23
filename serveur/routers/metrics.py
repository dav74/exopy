from fastapi import APIRouter, Depends, HTTPException
from core.security import get_current_user, AuthUser
from models.schemas import StudentMetrics, LogEvent
from core.database import get_db
import psycopg2.extras

router = APIRouter(tags=["metrics"])

@router.get('/api/metrics/{student_id}', response_model=StudentMetrics)
def get_student_metrics(student_id: str, current_user: AuthUser = Depends(get_current_user)):
    admin_id = current_user.admin_id

    if current_user.role == "student":
        if current_user.username != student_id:
            raise HTTPException(status_code=403, detail="Accès non autorisé.")
    elif current_user.role in ("admin", "superadmin"):
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM users WHERE username = %s AND admin_id = %s",
                    (student_id, admin_id)
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=403, detail="Élève non trouvé dans votre liste.")
    else:
        raise HTTPException(status_code=403, detail="Accès non autorisé.")

    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT exercise_id, status, created_at, session_id, error_type, duration FROM user_progress WHERE user_id = %s",
                    (student_id,)
                )
                logs = [dict(row) for row in cur.fetchall()]

                cur.execute(
                    "SELECT id, niveau FROM exercises WHERE admin_id = %s",
                    (admin_id,)
                )
                exercises_list = [dict(row) for row in cur.fetchall()]

        success_ex_ids = {log['exercise_id'] for log in logs if log['status'] == 'success'}
        total_completion = len(success_ex_ids)

        total_exercises = len(exercises_list)

        level_map = {"1": "Vert", "2": "Bleu", "3": "Rouge", "4": "Noir"}
        xp_weights = {"1": 10, "2": 20, "3": 40, "4": 80}

        ex_by_id = {ex['id']: str(ex['niveau']) for ex in exercises_list}
        levels_count = {"Vert": 0, "Bleu": 0, "Rouge": 0, "Noir": 0}
        xp = 0

        ai_req_ex_ids = {log['exercise_id'] for log in logs if log['status'] == 'ai_request'}

        for ex_id in success_ex_ids:
            niveau_id = ex_by_id.get(ex_id)
            if niveau_id in level_map:
                label = level_map[niveau_id]
                levels_count[label] += 1
                base_xp = xp_weights.get(niveau_id, 10)
                if ex_id not in ai_req_ex_ids:
                    xp += int(base_xp * 1.5)
                else:
                    xp += base_xp

        if total_completion > 0:
            success_no_ai = len(success_ex_ids - ai_req_ex_ids)
            success_rate_no_ai = (success_no_ai / total_completion) * 100
        else:
            success_rate_no_ai = 0.0

        total_ai_reqs = len([log for log in logs if log['status'] == 'ai_request'])
        avg_ai_requests = total_ai_reqs / total_exercises if total_exercises > 0 else 0

        badges_declic = 0
        sessions = {}
        for log in logs:
            sid = log['session_id']
            if sid not in sessions:
                sessions[sid] = []
            sessions[sid].append(log)

        for sid, s_logs in sessions.items():
            has_ai = any(l['status'] == 'ai_request' for l in s_logs)
            has_success = any(l['status'] == 'success' for l in s_logs)
            if has_ai and has_success:
                badges_declic += 1

        total_attempts = len([log for log in logs if log['status'] in ['success', 'failure']])

        first_tries = 0
        for ex_id in success_ex_ids:
            ex_attempts = [l for l in logs if l['exercise_id'] == ex_id and l['status'] in ['success', 'failure']]
            ex_attempts_sorted = sorted(ex_attempts, key=lambda x: x['created_at'])
            if ex_attempts_sorted and ex_attempts_sorted[0]['status'] == 'success':
                first_tries += 1

        first_try_rate = (first_tries / total_completion * 100) if total_completion > 0 else 0.0
        perseverance_index = (total_attempts / total_completion) if total_completion > 0 else 1.0

        error_counts = {}
        for log in logs:
            if log['error_type']:
                error_counts[log['error_type']] = error_counts.get(log['error_type'], 0) + 1

        common_errors = sorted(
            [{"type": k, "count": v} for k, v in error_counts.items()],
            key=lambda x: x['count'], reverse=True
        )[:3]

        if logs:
            from datetime import datetime, timedelta, timezone
            now = datetime.now(timezone.utc)
            one_week_ago = now - timedelta(days=7)

            weekly_logs = [
                l for l in logs
                if datetime.fromisoformat(str(l['created_at']).replace('Z', '+00:00')) > one_week_ago
            ]

            total_duration_secs = 0
            old_logs_count = 0
            for l in weekly_logs:
                d = l.get('duration')
                if d is not None:
                    total_duration_secs += d
                elif l.get('status') in ['success', 'failure']:
                    old_logs_count += 1

            weekly_practice_time = (total_duration_secs // 60) + (old_logs_count * 2)

            dates = sorted(
                {datetime.fromisoformat(str(log['created_at'])).date() for log in logs},
                reverse=True
            )
            streak = 0
            if dates:
                streak = 1
                for i in range(len(dates) - 1):
                    diff = (dates[i] - dates[i + 1]).days
                    if diff == 1:
                        streak += 1
                    else:
                        break
        else:
            streak = 0
            weekly_practice_time = 0

        return {
            "progression": {
                "total_completion": total_completion,
                "total_exercises": total_exercises,
                "levels": levels_count,
                "xp": xp
            },
            "autonomie": {
                "success_rate_no_ai": round(success_rate_no_ai, 1),
                "avg_ai_requests": round(avg_ai_requests, 1),
                "badges_declic": badges_declic
            },
            "qualite": {
                "first_try_rate": round(first_try_rate, 1),
                "perseverance_index": round(perseverance_index, 1),
                "common_errors": common_errors
            },
            "engagement": {
                "streak": streak,
                "weekly_practice_time": weekly_practice_time
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error calculating metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/api/metrics/log')
def log_metric_event(event: LogEvent, current_user: AuthUser = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO user_progress (user_id, exercise_id, status, error_type, session_id, duration)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (current_user.username, event.exercise_id, event.status, event.error_type, event.session_id, event.duration)
                )
        return {"success": True}
    except Exception as e:
        print(f"Failed to log metric: {e}")
        return {"success": False, "detail": str(e)}
