from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from core.database import get_db
from core.security import get_current_admin, get_current_superadmin, AuthUser
from models.schemas import (
    UserInfo, UserPasswordReset, UserUpdate, UserCreate,
    AdminCreate, AdminPasswordReset, AdminApiKeyUpdate, AdminPasswordChange, AdminOut
)
from passlib.hash import bcrypt
import psycopg2.extras
import csv
import io

router = APIRouter(prefix="/admin", tags=["admin_mgmt"])

def _hash_password(plain: str) -> str:
    return bcrypt.using(rounds=6).hash(plain)

@router.get("/profile")
def get_admin_profile(admin: AuthUser = Depends(get_current_admin)):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, username, openrouter_api_key IS NOT NULL as api_key_set, is_super FROM admins WHERE id = %s",
                    (admin.admin_id,)
                )
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Admin non trouvé")
                return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/profile/api-key")
def update_api_key(payload: AdminApiKeyUpdate, admin: AuthUser = Depends(get_current_admin)):
    try:
        api_key = payload.openrouter_api_key.strip() if payload.openrouter_api_key else None
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE admins SET openrouter_api_key = %s WHERE id = %s", (api_key, admin.admin_id))
        return {"success": True, "message": "Clé API mise à jour."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/profile/password")
def change_admin_password(payload: AdminPasswordChange, admin: AuthUser = Depends(get_current_admin)):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT password_hash FROM admins WHERE id = %s", (admin.admin_id,))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Admin non trouvé.")
                if not bcrypt.verify(payload.current_password, row['password_hash']):
                    raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect.")
                cur.execute(
                    "UPDATE admins SET password_hash = %s WHERE id = %s",
                    (_hash_password(payload.new_password), admin.admin_id)
                )
        return {"success": True, "message": "Mot de passe mis à jour."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users")
def create_single_user(payload: UserCreate, admin: AuthUser = Depends(get_current_admin)):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT username FROM users WHERE username = %s", (payload.username,))
                if cur.fetchone():
                    raise HTTPException(status_code=400, detail=f"L'utilisateur '{payload.username}' existe déjà.")

                cur.execute(
                    "INSERT INTO users (username, password_hash, nom, prenom, admin_id) VALUES (%s, %s, %s, %s, %s)",
                    (
                        payload.username.strip(),
                        _hash_password(payload.password),
                        payload.nom.strip() if payload.nom else "",
                        payload.prenom.strip() if payload.prenom else "",
                        admin.admin_id
                    )
                )
        return {"success": True, "message": f"Utilisateur '{payload.username}' créé avec succès."}
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
                    "SELECT username, nom, prenom FROM users WHERE admin_id = %s ORDER BY nom, prenom",
                    (admin.admin_id,)
                )
                return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des utilisateurs: {str(e)}")

@router.put("/users/{username}")
def update_user(username: str, payload: UserUpdate, admin: AuthUser = Depends(get_current_admin)):
    try:
        update_data = {k: v for k, v in payload.dict().items() if v is not None}
        if not update_data:
            return {"success": True, "message": "Aucune donnée à mettre à jour."}

        fields = ", ".join(f"{k} = %s" for k in update_data)
        values = list(update_data.values()) + [username, admin.admin_id]

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(f"UPDATE users SET {fields} WHERE username = %s AND admin_id = %s", values)
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail=f"Utilisateur '{username}' non trouvé.")

        return {"success": True, "message": f"Profil de {username} mis à jour."}
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
                    "UPDATE users SET password_hash = %s WHERE username = %s AND admin_id = %s",
                    (_hash_password(payload.new_password), payload.username, admin.admin_id)
                )
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail=f"Utilisateur '{payload.username}' non trouvé.")
        return {"success": True, "message": f"Mot de passe de {payload.username} mis à jour avec succès."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la réinitialisation : {str(e)}")

@router.post("/users/import")
async def import_users(file: UploadFile = File(...), admin: AuthUser = Depends(get_current_admin)):
    """
    Importe des utilisateurs à partir d'un fichier CSV.
    Format attendu : nom, prenom, login, password
    ATTENTION : efface les utilisateurs existants de cet admin et leur historique.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Le fichier doit être au format CSV.")

    try:
        content = await file.read()
        decoded = content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(decoded))

        rows = list(csv_reader)
        if not rows:
            raise HTTPException(status_code=400, detail="Le fichier est vide.")

        first_row = rows[0]
        start_index = 0
        if any(h.lower() in ['login', 'identifiant', 'mot de passe', 'password', 'nom', 'prénom'] for h in first_row):
            start_index = 1

        new_users = []
        for row in rows[start_index:]:
            if len(row) < 4:
                continue
            nom, prenom, login, password = [item.strip() for item in row[:4]]
            if not login or not password:
                continue
            new_users.append((login, _hash_password(password), nom, prenom, admin.admin_id))

        if not new_users:
            raise HTTPException(
                status_code=400,
                detail="Aucun utilisateur valide trouvé. Assurez-vous d'avoir 4 colonnes : nom, prenom, login, password."
            )

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM user_progress WHERE user_id IN (SELECT username FROM users WHERE admin_id = %s)",
                    (admin.admin_id,)
                )
                cur.execute("DELETE FROM users WHERE admin_id = %s", (admin.admin_id,))
                cur.executemany(
                    "INSERT INTO users (username, password_hash, nom, prenom, admin_id) VALUES (%s, %s, %s, %s, %s)",
                    new_users
                )

        return {
            "success": True,
            "message": f"{len(new_users)} utilisateurs importés. Les données précédentes de cet admin ont été effacées.",
            "count": len(new_users)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'import : {str(e)}")

# === Super-admin routes ===

@router.get("/admins", response_model=list[AdminOut])
def list_admins(superadmin: AuthUser = Depends(get_current_superadmin)):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT a.id, a.username, a.is_super,
                           a.openrouter_api_key IS NOT NULL as api_key_set,
                           (SELECT COUNT(*) FROM users u WHERE u.admin_id = a.id) as nb_students
                    FROM admins a ORDER BY a.id
                """)
                return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admins")
def create_admin(payload: AdminCreate, superadmin: AuthUser = Depends(get_current_superadmin)):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT id FROM admins WHERE username = %s", (payload.username,))
                if cur.fetchone():
                    raise HTTPException(status_code=400, detail=f"L'admin '{payload.username}' existe déjà.")

                cur.execute(
                    "INSERT INTO admins (username, password_hash, is_super) VALUES (%s, %s, FALSE) RETURNING id, username",
                    (payload.username.strip(), _hash_password(payload.password))
                )
                row = cur.fetchone()
        return {"success": True, "message": f"Admin '{payload.username}' créé avec succès.", "id": row['id']}
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
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE admins SET password_hash = %s WHERE id = %s AND is_super = FALSE",
                    (_hash_password(payload.new_password), payload.admin_id)
                )
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Admin non trouvé.")
        return {"success": True, "message": "Mot de passe admin réinitialisé."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
