from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

from routers import auth, exercises, llm, metrics, admin_mgmt

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="EXOPY API", description="API for learning Python with GenAI assistance")

_origins_env = os.getenv("CORS_ORIGINS", "")
if _origins_env:
    origins = [o.strip() for o in _origins_env.split(",") if o.strip()]
else:
    # Dev only — in production nginx serves frontend and API on the same origin
    origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(exercises.router)
app.include_router(llm.router)
app.include_router(metrics.router)
app.include_router(admin_mgmt.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to EXOPY API"}