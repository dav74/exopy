from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from core.database import get_db
from core.security import get_current_admin
from models.schemas import UserInfo, UserPasswordReset, UserUpdate, UserCreate
from passlib.hash import bcrypt
import psycopg2.extras
import csv
import io

router = APIRouter(prefix="/admin", tags=["admin_mgmt"])

def _hash_password(plain: str) -> str:
    return bcrypt.using(rounds=6).hash(plain)

@router.post("/users")
def create_single_user(payload: UserCreate, admin: str = Depends(get_current_admin)):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT username FROM users WHERE username = %s", (payload.username,))
                if cur.fetchone():
                    raise HTTPException(status_code=400, detail=f"L'utilisateur '{payload.username}' existe déjà.")

                cur.execute(
                    "INSERT INTO users (username, password_hash, nom, prenom) VALUES (%s, %s, %s, %s)",
                    (
                        payload.username.strip(),
                        _hash_password(payload.password),
                        payload.nom.strip() if payload.nom else "",
                        payload.prenom.strip() if payload.prenom else "",
                    )
                )
        return {"success": True, "message": f"Utilisateur '{payload.username}' créé avec succès."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création : {str(e)}")

@router.get("/users", response_model=list[UserInfo])
def list_users(admin: str = Depends(get_current_admin)):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT username, nom, prenom FROM users ORDER BY nom, prenom")
                return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des utilisateurs: {str(e)}")

@router.put("/users/{username}")
def update_user(username: str, payload: UserUpdate, admin: str = Depends(get_current_admin)):
    try:
        update_data = {k: v for k, v in payload.dict().items() if v is not None}
        if not update_data:
            return {"success": True, "message": "Aucune donnée à mettre à jour."}

        fields = ", ".join(f"{k} = %s" for k in update_data)
        values = list(update_data.values()) + [username]

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(f"UPDATE users SET {fields} WHERE username = %s", values)
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail=f"Utilisateur '{username}' non trouvé.")

        return {"success": True, "message": f"Profil de {username} mis à jour."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour : {str(e)}")

@router.delete("/users/{username}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(username: str, admin: str = Depends(get_current_admin)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM user_progress WHERE user_id = %s", (username,))
                cur.execute("DELETE FROM users WHERE username = %s", (username,))
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail=f"Utilisateur '{username}' non trouvé.")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression : {str(e)}")

@router.post("/users/reset-password")
def reset_password(payload: UserPasswordReset, admin: str = Depends(get_current_admin)):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET password_hash = %s WHERE username = %s",
                    (_hash_password(payload.new_password), payload.username)
                )
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail=f"Utilisateur '{payload.username}' non trouvé.")
        return {"success": True, "message": f"Mot de passe de {payload.username} mis à jour avec succès."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la réinitialisation : {str(e)}")

@router.post("/users/import")
async def import_users(file: UploadFile = File(...), admin: str = Depends(get_current_admin)):
    """
    Importe des utilisateurs à partir d'un fichier CSV.
    Format attendu : nom, prenom, login, password
    ATTENTION : efface TOUS les utilisateurs et TOUTES les activités existantes.
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
            new_users.append((login, _hash_password(password), nom, prenom))

        if not new_users:
            raise HTTPException(
                status_code=400,
                detail="Aucun utilisateur valide trouvé. Assurez-vous d'avoir 4 colonnes : nom, prenom, login, password."
            )

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM user_progress")
                cur.execute("DELETE FROM users")
                cur.executemany(
                    "INSERT INTO users (username, password_hash, nom, prenom) VALUES (%s, %s, %s, %s)",
                    new_users
                )

        return {
            "success": True,
            "message": f"{len(new_users)} utilisateurs importés. Toutes les données précédentes ont été effacées.",
            "count": len(new_users)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'import : {str(e)}")
