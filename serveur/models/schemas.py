from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class Login(BaseModel):
    username: str
    password: str

class RequestExercise(BaseModel):
    session: str
    enonce: str
    code: str
    res_test: str
    is_assistant: bool

class LogEvent(BaseModel):
    exercise_id: int
    status: str # 'success', 'failure', 'ai_request'
    error_type: str | None = None
    session_id: str
    duration: int | None = None

class ExerciseCreate(BaseModel):
    titre: str
    niveau: str | int
    enonce: str
    test: str
    ordering: int | None = None

class ExerciseUpdate(BaseModel):
    titre: str | None = None
    niveau: str | int | None = None
    enonce: str | None = None
    test: str | None = None
    ordering: int | None = None

class ExerciseReorder(BaseModel):
    ids: list[int]

class ExerciseAIRequest(BaseModel):
    difficulty: str
    existing_titles: list[str]

# --- Metrics Models ---

class ProgressionMetrics(BaseModel):
    total_completion: int
    total_exercises: int
    levels: dict[str, int]
    xp: int

class AutonomieMetrics(BaseModel):
    success_rate_no_ai: float
    avg_ai_requests: float
    badges_declic: int

class ErrorTypeCount(BaseModel):
    type: str
    count: int

class QualiteMetrics(BaseModel):
    first_try_rate: float
    perseverance_index: float
    common_errors: list[ErrorTypeCount]

class EngagementMetrics(BaseModel):
    streak: int
    weekly_practice_time: int # in minutes

class StudentMetrics(BaseModel):
    progression: ProgressionMetrics
    autonomie: AutonomieMetrics
    qualite: QualiteMetrics
    engagement: EngagementMetrics

# --- Admin User Management ---

class UserInfo(BaseModel):
    username: str
    nom: str | None = None
    prenom: str | None = None

class UserCreate(BaseModel):
    username: str
    password: str
    nom: str | None = None
    prenom: str | None = None

class UserUpdate(BaseModel):
    nom: str | None = None
    prenom: str | None = None

class UserPasswordReset(BaseModel):
    username: str
    new_password: str
