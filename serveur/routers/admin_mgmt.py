from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from core.database import get_db
from core.security import get_current_admin, get_current_superadmin, AuthUser
from models.schemas import (
    UserInfo, UserPasswordReset, UserUpdate, UserCreate,
    AdminCreate, AdminUpdate, AdminPasswordReset, AdminOut, ConsentUpdate
)
from passlib.hash import bcrypt
import psycopg2.extras
import csv
import io
import unicodedata

router = APIRouter(prefix="/admin", tags=["admin_mgmt"])

def _hash_password(plain: str) -> str:
    return bcrypt.using(rounds=6).hash(plain)

def _remove_accents(text: str) -> str:
    if not text:
        return ""
    nfkd = unicodedata.normalize('NFKD', text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))

def _generate_login(nom: str, prenom: str, existing_logins: set) -> str:
    nom_clean = _remove_accents(nom).lower().replace(" ", "").replace("-", "")
    prenom_clean = _remove_accents(prenom).lower().replace(" ", "").replace("-", "")
    base_login = (nom_clean[:6] + prenom_clean[0]) if prenom_clean else nom_clean[:7]

    login = base_login
    counter = 1
    while login in existing_logins:
        login = f"{base_login}{counter}"
        counter += 1

    existing_logins.add(login)
    return login

@router.post("/users")
def create_single_user(payload: UserCreate, admin: AuthUser = Depends(get_current_admin)):
    try:
        username = payload.username.strip()
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT username FROM users WHERE username = %s", (username,))
                if cur.fetchone():
                    raise HTTPException(status_code=400, detail=f"L'utilisateur '{username}' existe déjà.")

                cur.execute(
                    "INSERT INTO users (username, password_hash, nom, prenom, admin_id, must_change_password) VALUES (%s, %s, %s, %s, %s, TRUE)",
                    (
                        username,
                        _hash_password(username),
                        payload.nom.strip() if payload.nom else "",
                        payload.prenom.strip() if payload.prenom else "",
                        admin.admin_id
                    )
                )
        return {"success": True, "message": f"Utilisateur '{username}' créé avec succès."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création : {str(e)}")

@router.get("/users", response_model=list[UserInfo])
def list_users(admin: AuthUser = Depends(get_current_admin)):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """SELECT u.username, u.nom, u.prenom, u.must_change_password,
                              COALESCE(rc.consent_given, FALSE) AS consent_given
                       FROM users u
                       LEFT JOIN research_consent rc ON rc.user_id = u.username
                       WHERE u.admin_id = %s ORDER BY u.nom, u.prenom""",
                    (admin.admin_id,)
                )
                return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des utilisateurs: {str(e)}")

@router.put("/users/{username}/consent")
def set_research_consent(username: str, payload: ConsentUpdate, admin: AuthUser = Depends(get_current_admin)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE username = %s AND admin_id = %s", (username, admin.admin_id))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Élève non trouvé dans votre liste.")

                if payload.consent_given:
                    cur.execute(
                        """INSERT INTO research_consent (user_id, consent_given, recorded_by, consented_at, revoked_at)
                           VALUES (%s, TRUE, %s, NOW(), NULL)
                           ON CONFLICT (user_id) DO UPDATE
                           SET consent_given = TRUE, recorded_by = EXCLUDED.recorded_by, consented_at = NOW(), revoked_at = NULL""",
                        (username, admin.username)
                    )
                else:
                    cur.execute(
                        """INSERT INTO research_consent (user_id, consent_given, recorded_by, revoked_at)
                           VALUES (%s, FALSE, %s, NOW())
                           ON CONFLICT (user_id) DO UPDATE
                           SET consent_given = FALSE, recorded_by = EXCLUDED.recorded_by, revoked_at = NOW()""",
                        (username, admin.username)
                    )
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour du consentement: {str(e)}")

ALLOWED_USER_UPDATE_FIELDS = {"nom", "prenom", "username"}

@router.put("/users/{username}")
def update_user(username: str, payload: UserUpdate, admin: AuthUser = Depends(get_current_admin)):
    try:
        update_data = {k: v for k, v in payload.dict().items() if v is not None and k in ALLOWED_USER_UPDATE_FIELDS}
        if not update_data:
            return {"success": True, "message": "Aucune donnée à mettre à jour."}

        new_username = update_data.get("username")
        if new_username is not None:
            new_username = new_username.strip()
            if not new_username:
                raise HTTPException(status_code=400, detail="L'identifiant ne peut pas être vide.")

        with get_db() as conn:
            with conn.cursor() as cur:
                if new_username is not None and new_username != username:
                    cur.execute("SELECT id FROM users WHERE username = %s", (new_username,))
                    if cur.fetchone():
                        raise HTTPException(status_code=400, detail=f"L'identifiant '{new_username}' existe déjà.")

                cur.execute(
                    "UPDATE users SET nom = COALESCE(%s, nom), prenom = COALESCE(%s, prenom), username = COALESCE(%s, username) WHERE username = %s AND admin_id = %s",
                    (update_data.get("nom"), update_data.get("prenom"), new_username, username, admin.admin_id)
                )
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail=f"Utilisateur '{username}' non trouvé.")

        return {"success": True, "message": f"Profil de {new_username or username} mis à jour."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour : {str(e)}")

@router.delete("/users/{username}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(username: str, admin: AuthUser = Depends(get_current_admin)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM user_progress WHERE user_id IN (SELECT username FROM users WHERE username = %s AND admin_id = %s)", (username, admin.admin_id))
                cur.execute("DELETE FROM users WHERE username = %s AND admin_id = %s", (username, admin.admin_id))
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail=f"Utilisateur '{username}' non trouvé.")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression : {str(e)}")

@router.post("/users/reset-password")
def reset_password(payload: UserPasswordReset, admin: AuthUser = Depends(get_current_admin)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET password_hash = %s, must_change_password = TRUE WHERE username = %s AND admin_id = %s",
                    (_hash_password(payload.username), payload.username, admin.admin_id)
                )
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail=f"Utilisateur '{payload.username}' non trouvé.")
        return {"success": True, "message": f"Mot de passe de {payload.username} réinitialisé (identique à l'identifiant)."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la réinitialisation : {str(e)}")

@router.post("/users/import")
async def import_users(file: UploadFile = File(...), admin: AuthUser = Depends(get_current_admin)):
    """
    Importe des utilisateurs à partir d'un fichier CSV.
    Format attendu : nom, prenom (les colonnes suivantes, le cas échéant, sont ignorées).
    Le login est généré automatiquement (mêmes règles que le script prepare_import.py : 6 premières lettres
    du nom + 1ère lettre du prénom, sans accents, suffixe numérique en cas de collision) et sert aussi de
    mot de passe initial. L'admin peut ensuite modifier ce login via le formulaire d'édition de l'élève.
    Le fichier représente l'état complet de la liste des élèves : les élèves déjà présents (même nom + prénom) sont
    conservés tels quels (mot de passe et historique intacts), les élèves absents du fichier sont créés,
    et les élèves existants qui ne sont PAS dans le fichier sont supprimés (avec leur historique).
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Le fichier doit être au format CSV.")

    try:
        content = await file.read()
        decoded = content.decode('utf-8')
        try:
            dialect = csv.Sniffer().sniff(decoded[:2048], delimiters=',;\t')
        except csv.Error:
            dialect = csv.excel
        csv_reader = csv.reader(io.StringIO(decoded), dialect)

        rows = list(csv_reader)
        if not rows:
            raise HTTPException(status_code=400, detail="Le fichier est vide.")

        first_row = rows[0]
        start_index = 0
        if any(h.lower() in ['login', 'identifiant', 'mot de passe', 'password', 'nom', 'prénom'] for h in first_row):
            start_index = 1

        parsed_rows = []
        for row in rows[start_index:]:
            if len(row) < 2:
                continue
            nom, prenom = [item.strip() for item in row[:2]]
            if not nom or not prenom:
                continue
            parsed_rows.append((nom, prenom))

        if not parsed_rows:
            raise HTTPException(
                status_code=400,
                detail="Aucun utilisateur valide trouvé. Assurez-vous d'avoir au moins 2 colonnes : nom, prenom."
            )

        created_count = 0
        kept_count = 0
        kept_usernames = set()
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT username FROM users")
                existing_logins = {row[0] for row in cur.fetchall()}

                for nom, prenom in parsed_rows:
                    cur.execute(
                        "SELECT username FROM users WHERE admin_id = %s AND LOWER(nom) = LOWER(%s) AND LOWER(prenom) = LOWER(%s)",
                        (admin.admin_id, nom, prenom)
                    )
                    row = cur.fetchone()
                    if row:
                        kept_usernames.add(row[0])
                        kept_count += 1
                        continue

                    login = _generate_login(nom, prenom, existing_logins)
                    cur.execute(
                        "INSERT INTO users (username, password_hash, nom, prenom, admin_id, must_change_password) VALUES (%s, %s, %s, %s, %s, TRUE)",
                        (login, _hash_password(login), nom, prenom, admin.admin_id)
                    )
                    kept_usernames.add(login)
                    created_count += 1

                cur.execute("SELECT username FROM users WHERE admin_id = %s", (admin.admin_id,))
                all_admin_usernames = {row[0] for row in cur.fetchall()}
                usernames_to_delete = list(all_admin_usernames - kept_usernames)

                deleted_count = len(usernames_to_delete)
                if usernames_to_delete:
                    cur.execute("DELETE FROM user_progress WHERE user_id = ANY(%s)", (usernames_to_delete,))
                    cur.execute("DELETE FROM users WHERE username = ANY(%s)", (usernames_to_delete,))

        message = (
            f"{created_count} élève(s) créé(s), {kept_count} déjà présent(s) conservé(s) avec leur historique, "
            f"{deleted_count} supprimé(s) (absent(s) du fichier)."
        )

        return {
            "success": True,
            "message": message,
            "created": created_count,
            "kept": kept_count,
            "deleted": deleted_count,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'import : {str(e)}")

@router.get("/student-history/{student_id}")
def get_student_history(student_id: str, admin: AuthUser = Depends(get_current_admin)):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT 1 FROM users WHERE username = %s AND admin_id = %s",
                    (student_id, admin.admin_id)
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Élève non trouvé.")

                cur.execute(
                    """SELECT up.id, up.exercise_id, up.status, up.error_type, up.session_id, up.duration, up.created_at,
                              e.titre as exercise_title, e.niveau as exercise_niveau, e.ordering as exercise_ordering
                       FROM user_progress up
                       JOIN exercises e ON e.id = up.exercise_id
                       WHERE up.user_id = %s
                       ORDER BY up.created_at ASC""",
                    (student_id,)
                )
                all_rows = []
                for row in cur.fetchall():
                    d = dict(row)
                    if d.get('created_at'):
                        d['created_at'] = d['created_at'].isoformat()
                    all_rows.append(d)

        exercise_events = {}
        for event in all_rows:
            eid = event['exercise_id']
            if eid not in exercise_events:
                exercise_events[eid] = []
            exercise_events[eid].append(event)

        attempts = []
        for eid, events in exercise_events.items():
            current = []
            attempt_number = 0
            last_passage = None
            for event in events:
                current.append(event)
                if event['status'] == 'success':
                    attempt_number += 1
                    last_passage = _make_attempt(current, attempt_number)
                    attempts.append(last_passage)
                    current = []
            if current:
                # Une requête IA isolée après une réussite (ex: le bilan) ne constitue
                # pas un nouveau passage : elle est rattachée au dernier passage réussi.
                if last_passage is not None and all(e['status'] == 'ai_request' for e in current):
                    last_passage['ai_requests'] += len(current)
                    last_passage['last_attempt_at'] = current[-1]['created_at']
                else:
                    attempt_number += 1
                    attempts.append(_make_attempt(current, attempt_number))

        attempts.sort(key=lambda a: (a['exercise_ordering'], a['first_attempt_at']))

        # La chronologie n'affiche que les tentatives (réussite/échec) ; une requête IA
        # isolée est rattachée à la tentative qui l'a déclenchée plutôt que d'apparaître
        # comme une ligne à part.
        submission_events = []
        for events in exercise_events.values():
            pending = None
            for event in events:
                if event['status'] in ('success', 'failure'):
                    if pending is not None:
                        submission_events.append(pending)
                    pending = dict(event)
                    pending['ai_used'] = False
                elif event['status'] == 'ai_request' and pending is not None:
                    pending['ai_used'] = True
            if pending is not None:
                submission_events.append(pending)

        events_desc = sorted(submission_events, key=lambda e: e['created_at'], reverse=True)

        return {"attempts": attempts, "events": events_desc}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _make_attempt(events, attempt_number):
    total_attempts = len([e for e in events if e['status'] in ('success', 'failure')])
    ai_requests = len([e for e in events if e['status'] == 'ai_request'])
    solved = any(e['status'] == 'success' for e in events)
    solved_at = next((e['created_at'] for e in events if e['status'] == 'success'), None)
    total_duration = sum(e.get('duration') or 0 for e in events)
    return {
        'exercise_id': events[0]['exercise_id'],
        'exercise_title': events[0]['exercise_title'],
        'exercise_niveau': events[0]['exercise_niveau'],
        'exercise_ordering': events[0].get('exercise_ordering', 0),
        'attempt_number': attempt_number,
        'total_attempts': total_attempts,
        'ai_requests': ai_requests,
        'first_attempt_at': events[0]['created_at'],
        'last_attempt_at': events[-1]['created_at'],
        'solved': solved,
        'solved_at': solved_at,
        'total_duration': total_duration,
    }

# === Super-admin routes ===

@router.get("/admins", response_model=list[AdminOut])
def list_admins(superadmin: AuthUser = Depends(get_current_superadmin)):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT a.id, a.username, a.nom, a.prenom, a.etablissement, a.email, a.is_super, a.must_change_password,
                           (SELECT COUNT(*) FROM users u WHERE u.admin_id = a.id) as nb_students,
                           (SELECT COUNT(*) FROM exercises e WHERE e.admin_id = a.id) as nb_exercises,
                           (SELECT COUNT(*) FROM user_progress up
                            JOIN users u ON up.user_id = u.username
                            WHERE u.admin_id = a.id AND up.status = 'ai_request') as nb_ai_requests,
                           (SELECT COUNT(*) FROM user_progress up
                            JOIN users u ON up.user_id = u.username
                            WHERE u.admin_id = a.id) as nb_total_requests,
                           (SELECT MAX(up.created_at) FROM user_progress up
                            JOIN users u ON up.user_id = u.username
                            WHERE u.admin_id = a.id) as last_activity
                    FROM admins a ORDER BY a.id
                """)
                rows = cur.fetchall()
                result = []
                for row in rows:
                    d = dict(row)
                    d['last_activity'] = d['last_activity'].isoformat() if d['last_activity'] else None
                    result.append(d)
                return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admins")
def create_admin(payload: AdminCreate, superadmin: AuthUser = Depends(get_current_superadmin)):
    try:
        username = payload.username.strip()
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT id FROM admins WHERE username = %s", (username,))
                if cur.fetchone():
                    raise HTTPException(status_code=400, detail=f"L'admin '{username}' existe déjà.")

                cur.execute(
                    """INSERT INTO admins (username, password_hash, nom, prenom, etablissement, email, is_super, must_change_password)
                       VALUES (%s, %s, %s, %s, %s, %s, FALSE, TRUE) RETURNING id, username""",
                    (
                        username,
                        _hash_password(username),
                        payload.nom.strip() if payload.nom else "",
                        payload.prenom.strip() if payload.prenom else "",
                        payload.etablissement.strip() if payload.etablissement else None,
                        payload.email.strip() if payload.email else None,
                    )
                )
                row = cur.fetchone()
        return {"success": True, "message": f"Admin '{username}' créé avec succès.", "id": row['id']}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/admins/{admin_id}")
def update_admin(admin_id: int, payload: AdminUpdate, superadmin: AuthUser = Depends(get_current_superadmin)):
    username = payload.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="L'identifiant ne peut pas être vide.")
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT id FROM admins WHERE id = %s AND is_super = FALSE", (admin_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Admin non trouvé.")

                cur.execute("SELECT id FROM admins WHERE username = %s AND id != %s", (username, admin_id))
                if cur.fetchone():
                    raise HTTPException(status_code=400, detail=f"L'admin '{username}' existe déjà.")

                cur.execute(
                    "UPDATE admins SET username = %s, nom = %s, prenom = %s, etablissement = %s, email = %s WHERE id = %s",
                    (
                        username,
                        payload.nom.strip() if payload.nom else "",
                        payload.prenom.strip() if payload.prenom else "",
                        payload.etablissement.strip() if payload.etablissement else None,
                        payload.email.strip() if payload.email else None,
                        admin_id
                    )
                )
        return {"success": True, "message": "Admin mis à jour."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/admins/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin(admin_id: int, superadmin: AuthUser = Depends(get_current_superadmin)):
    if admin_id == superadmin.admin_id:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas supprimer votre propre compte.")
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM admins WHERE id = %s AND is_super = FALSE", (admin_id,))
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Admin non trouvé ou super-admin.")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admins/reset-password")
def reset_admin_password(payload: AdminPasswordReset, superadmin: AuthUser = Depends(get_current_superadmin)):
    if payload.admin_id == superadmin.admin_id:
        raise HTTPException(status_code=400, detail="Utilisez les variables d'environnement pour changer votre mot de passe.")
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT username FROM admins WHERE id = %s AND is_super = FALSE", (payload.admin_id,))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Admin non trouvé.")
                cur.execute(
                    "UPDATE admins SET password_hash = %s, must_change_password = TRUE WHERE id = %s",
                    (_hash_password(row['username']), payload.admin_id)
                )
        return {"success": True, "message": "Mot de passe admin réinitialisé (identique à l'identifiant)."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
