from fastapi import APIRouter, Depends, HTTPException
from core.security import get_current_user, get_current_admin, AuthUser
from models.schemas import StudentMetrics, LogEvent
from core.database import get_db
from datetime import datetime, timedelta, timezone
import bisect
import psycopg2.extras

router = APIRouter(tags=["metrics"])

@router.get('/api/metrics/class')
def get_class_metrics(admin: AuthUser = Depends(get_current_admin)):
    admin_id = admin.admin_id
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """SELECT u.username, u.nom, u.prenom, COALESCE(rc.consent_given, FALSE) AS consent_given
                       FROM users u
                       LEFT JOIN research_consent rc ON rc.user_id = u.username
                       WHERE u.admin_id = %s ORDER BY u.nom, u.prenom""",
                    (admin_id,)
                )
                students = [dict(row) for row in cur.fetchall()]

                cur.execute(
                    "SELECT id, titre, niveau FROM exercises WHERE admin_id = %s ORDER BY ordering, id",
                    (admin_id,)
                )
                exercises_list = [dict(row) for row in cur.fetchall()]

                usernames = [s['username'] for s in students]
                logs = []
                if usernames and exercises_list:
                    cur.execute(
                        """SELECT user_id, exercise_id, status, error_type, created_at
                           FROM user_progress
                           WHERE user_id = ANY(%s) AND exercise_id = ANY(%s)""",
                        (usernames, [ex['id'] for ex in exercises_list])
                    )
                    logs = [dict(row) for row in cur.fetchall()]

        exercise_ids = [ex['id'] for ex in exercises_list]
        ex_titles = {ex['id']: ex['titre'] for ex in exercises_list}

        logs_by_user = {}
        for log in logs:
            logs_by_user.setdefault(log['user_id'], []).append(log)

        now = datetime.now(timezone.utc)
        heatmap = {}
        alerts = []

        for s in students:
            uname = s['username']
            user_logs = logs_by_user.get(uname, [])
            status_by_ex = {}

            for ex_id in exercise_ids:
                ex_attempts = [l for l in user_logs if l['exercise_id'] == ex_id and l['status'] in ('success', 'failure')]
                if not ex_attempts:
                    status_by_ex[ex_id] = "not_started"
                elif any(l['status'] == 'success' for l in ex_attempts):
                    status_by_ex[ex_id] = "success_hard" if len(ex_attempts) > 4 else "success"
                else:
                    status_by_ex[ex_id] = "failure"

                    fails = [l for l in ex_attempts if l['status'] == 'failure']
                    if len(fails) >= 3:
                        alerts.append({
                            "username": uname, "type": "stuck",
                            "exercise_id": ex_id, "exercise_title": ex_titles.get(ex_id),
                            "attempts": len(fails)
                        })
            heatmap[uname] = status_by_ex

            if user_logs:
                last_activity = max(l['created_at'] for l in user_logs)
                if last_activity.tzinfo is None:
                    last_activity = last_activity.replace(tzinfo=timezone.utc)
                days_inactive = (now - last_activity).days
                if days_inactive >= 7:
                    alerts.append({"username": uname, "type": "inactive", "days": days_inactive})

        exercise_stats = []
        for ex in exercises_list:
            ex_id = ex['id']
            ex_logs = [l for l in logs if l['exercise_id'] == ex_id]
            attempts = [l for l in ex_logs if l['status'] in ('success', 'failure')]
            attempters = {l['user_id'] for l in attempts}
            successes_by_user = {l['user_id'] for l in ex_logs if l['status'] == 'success'}
            ai_reqs = len([l for l in ex_logs if l['status'] == 'ai_request'])

            success_rate = (len(successes_by_user) / len(attempters) * 100) if attempters else 0.0
            avg_attempts = (len(attempts) / len(attempters)) if attempters else 0.0
            avg_ai = (ai_reqs / len(attempters)) if attempters else 0.0

            exercise_stats.append({
                "exercise_id": ex_id,
                "titre": ex['titre'],
                "niveau": ex['niveau'],
                "nb_attempters": len(attempters),
                "success_rate": round(success_rate, 1),
                "avg_attempts": round(avg_attempts, 1),
                "avg_ai_requests": round(avg_ai, 1)
            })

        error_counts = {}
        for log in logs:
            if log.get('error_type'):
                error_counts[log['error_type']] = error_counts.get(log['error_type'], 0) + 1
        error_distribution = sorted(
            [{"type": k, "count": v} for k, v in error_counts.items()],
            key=lambda x: x['count'], reverse=True
        )

        nb_consenting = len([s for s in students if s['consent_given']])

        return {
            "students": students,
            "exercises": [{"id": ex['id'], "titre": ex['titre'], "niveau": ex['niveau']} for ex in exercises_list],
            "heatmap": heatmap,
            "alerts": alerts,
            "exercise_stats": exercise_stats,
            "error_distribution": error_distribution,
            "consent_summary": {"given": nb_consenting, "total": len(students)}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

        attempted_ex_ids = {log['exercise_id'] for log in logs if log['status'] in ('success', 'failure')}
        total_ai_reqs = len([log for log in logs if log['status'] == 'ai_request'])
        avg_ai_requests = total_ai_reqs / len(attempted_ex_ids) if attempted_ex_ids else 0

        badges_declic = 0
        ex_sessions = {}
        for log in logs:
            key = log['exercise_id']
            if key not in ex_sessions:
                ex_sessions[key] = []
            ex_sessions[key].append(log)

        for ex_id, ex_logs in ex_sessions.items():
            has_ai = any(l['status'] == 'ai_request' for l in ex_logs)
            has_success = any(l['status'] == 'success' for l in ex_logs)
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

        NUM_WEEKS = 8
        now_dt = datetime.now(timezone.utc)
        current_week_start = now_dt.date() - timedelta(days=now_dt.weekday())
        week_starts = [current_week_start - timedelta(weeks=w) for w in range(NUM_WEEKS - 1, -1, -1)]

        def _parse_dt(raw):
            dt = datetime.fromisoformat(str(raw).replace('Z', '+00:00')) if isinstance(raw, str) else raw
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt

        buckets = [{"completed": 0, "completed_no_ai": 0, "attempts": 0, "ai_requests": 0} for _ in week_starts]

        for log in logs:
            log_date = _parse_dt(log['created_at']).date()
            idx = bisect.bisect_right(week_starts, log_date) - 1
            if idx < 0:
                continue
            bucket = buckets[idx]
            if log['status'] == 'success':
                bucket['completed'] += 1
                bucket['attempts'] += 1
                if log['exercise_id'] not in ai_req_ex_ids:
                    bucket['completed_no_ai'] += 1
            elif log['status'] == 'failure':
                bucket['attempts'] += 1
            elif log['status'] == 'ai_request':
                bucket['ai_requests'] += 1

        trends = [
            {
                "week_start": ws.isoformat(),
                "exercises_completed": b['completed'],
                "success_rate_no_ai": round(b['completed_no_ai'] / b['completed'] * 100, 1) if b['completed'] > 0 else 0.0,
                "ai_requests_per_attempt": round(b['ai_requests'] / b['attempts'], 1) if b['attempts'] > 0 else 0.0,
                "has_activity": b['attempts'] > 0 or b['ai_requests'] > 0
            }
            for ws, b in zip(week_starts, buckets)
        ]

        if logs:
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
                today = now.date()
                most_recent = dates[0]
                if (today - most_recent).days <= 1:
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
            },
            "trends": trends
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
                    """INSERT INTO user_progress (user_id, exercise_id, status, error_type, session_id, duration, code)
                       VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                    (current_user.username, event.exercise_id, event.status, event.error_type, event.session_id, event.duration, event.code)
                )
                new_id = cur.fetchone()[0]
                if event.status == "ai_request":
                    cur.execute(
                        """UPDATE user_progress SET ai_used = TRUE
                           WHERE id = (
                               SELECT id FROM user_progress
                               WHERE user_id = %s AND exercise_id = %s AND session_id = %s
                                 AND status IN ('success', 'failure')
                               ORDER BY created_at DESC LIMIT 1
                           )""",
                        (current_user.username, event.exercise_id, event.session_id)
                    )
        return {"success": True, "id": new_id}
    except Exception as e:
        print(f"Failed to log metric: {e}")
        return {"success": False, "detail": str(e)}
