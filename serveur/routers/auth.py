from fastapi import APIRouter, Depends, HTTPException, status
import os
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from core.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from core.database import get_db
from models.schemas import Token, UserInfo
from core.security import get_current_user
from passlib.hash import bcrypt
import psycopg2.extras

router = APIRouter(prefix="/auth", tags=["auth"])

def check_user(username: str, password: str) -> bool:
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
                row = cur.fetchone()
                if not row:
                    return False
                return bcrypt.verify(password, row['password_hash'])
    except Exception as e:
        print(f"Erreur lors de la vérification du mot de passe: {e}")
        return False

@router.post("/login/guest", response_model=Token)
async def login_guest():
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": "Invité"}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

    if ADMIN_USERNAME and ADMIN_PASSWORD and form_data.username == ADMIN_USERNAME and form_data.password == ADMIN_PASSWORD:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": form_data.username, "role": "admin"}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    if not check_user(form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username, "role": "student"}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserInfo)
async def get_me(username: str = Depends(get_current_user)):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT username, nom, prenom FROM users WHERE username = %s",
                    (username,)
                )
                row = cur.fetchone()
                if not row:
                    return {"username": username, "nom": "", "prenom": ""}
                return dict(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
