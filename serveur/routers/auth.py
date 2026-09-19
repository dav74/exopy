from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from core.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, AuthUser, get_current_user
from core.database import get_db
from models.schemas import Token, UserInfo, AdminPasswordChange
from services.settings import is_ai_configured
from passlib.hash import bcrypt
import psycopg2.extras

router = APIRouter(prefix="/auth", tags=["auth"])

def check_user(username: str, password: str):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT password_hash, admin_id FROM users WHERE username = %s", (username,))
                row = cur.fetchone()
                if not row:
                    return None
                if bcrypt.verify(password, row['password_hash']):
                    return row['admin_id']
                return None
    except Exception as e:
        print(f"Erreur lors de la vérification du mot de passe: {e}")
        return None

def check_admin(username: str, password: str):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT id, password_hash, is_super FROM admins WHERE username = %s", (username,))
                row = cur.fetchone()
                if not row:
                    return None
                if bcrypt.verify(password, row['password_hash']):
                    return {"admin_id": row['id'], "is_super": row['is_super']}
                return None
    except Exception as e:
        print(f"Erreur lors de la vérification du mot de passe admin: {e}")
        return None

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    admin_data = check_admin(form_data.username, form_data.password)
    if admin_data:
        role = "superadmin" if admin_data['is_super'] else "admin"
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": form_data.username, "role": role, "admin_id": admin_data['admin_id']},
            expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    admin_id = check_user(form_data.username, form_data.password)
    if admin_id is not None:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": form_data.username, "role": "student", "admin_id": admin_id},
            expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

@router.get("/me", response_model=UserInfo)
async def get_me(current_user: AuthUser = Depends(get_current_user)):
    ai_enabled = is_ai_configured()

    if current_user.role in ("admin", "superadmin"):
        try:
            with get_db() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("SELECT nom, prenom, must_change_password, ai_locked_by_super FROM admins WHERE id = %s", (current_user.admin_id,))
                    row = cur.fetchone()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        return {
            "username": current_user.username,
            "nom": row['nom'] if row else "",
            "prenom": row['prenom'] if row else "",
            "ai_enabled": ai_enabled and not (row and row['ai_locked_by_super']),
            "ai_locked_by_super": bool(row['ai_locked_by_super']) if row else False,
            "role": current_user.role,
            "must_change_password": bool(row['must_change_password']) if row else False,
        }

    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """SELECT u.username, u.nom, u.prenom, u.must_change_password, u.ai_disabled, a.ai_disabled AS admin_ai_disabled, a.ai_locked_by_super
                       FROM users u JOIN admins a ON a.id = u.admin_id
                       WHERE u.username = %s""",
                    (current_user.username,)
                )
                row = cur.fetchone()
                if not row:
                    return {"username": current_user.username, "nom": "", "prenom": "", "ai_enabled": False, "role": "student"}
                data = dict(row)
                admin_ai_disabled = data.pop("admin_ai_disabled")
                ai_locked = data.pop("ai_locked_by_super")
                return data | {"ai_enabled": ai_enabled and not row['ai_disabled'] and not admin_ai_disabled and not ai_locked, "role": "student"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/password")
def change_own_password(payload: AdminPasswordChange, current_user: AuthUser = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if current_user.role == "student":
                    cur.execute("SELECT password_hash FROM users WHERE username = %s", (current_user.username,))
                    row = cur.fetchone()
                    if not row:
                        raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")
                    if not bcrypt.verify(payload.current_password, row['password_hash']):
                        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect.")
                    cur.execute(
                        "UPDATE users SET password_hash = %s, must_change_password = FALSE WHERE username = %s",
                        (bcrypt.using(rounds=12).hash(payload.new_password), current_user.username)
                    )
                else:
                    cur.execute("SELECT password_hash FROM admins WHERE id = %s", (current_user.admin_id,))
                    row = cur.fetchone()
                    if not row:
                        raise HTTPException(status_code=404, detail="Admin non trouvé.")
                    if not bcrypt.verify(payload.current_password, row['password_hash']):
                        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect.")
                    cur.execute(
                        "UPDATE admins SET password_hash = %s, must_change_password = FALSE WHERE id = %s",
                        (bcrypt.using(rounds=12).hash(payload.new_password), current_user.admin_id)
                    )
        return {"success": True, "message": "Mot de passe mis à jour."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
