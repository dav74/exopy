from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from core.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, AuthUser, get_current_user
from core.database import get_db
from models.schemas import Token, UserInfo
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

@router.post("/login/guest", response_model=Token)
async def login_guest():
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": "Invité"}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

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
    ai_enabled = bool(os.getenv("OPENROUTER_API_KEY"))

    if current_user.role in ("admin", "superadmin"):
        return {
            "username": current_user.username,
            "nom": "",
            "prenom": "",
            "ai_enabled": ai_enabled,
            "role": current_user.role,
        }

    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT username, nom, prenom FROM users WHERE username = %s",
                    (current_user.username,)
                )
                row = cur.fetchone()
                if not row:
                    return {"username": current_user.username, "nom": "", "prenom": "", "ai_enabled": False, "role": "student"}
                return dict(row) | {"ai_enabled": ai_enabled, "role": "student"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
