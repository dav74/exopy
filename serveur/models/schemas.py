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
    exercise_id: int | None = None
    # id de la ligne user_progress (renvoyé par POST /api/metrics/log) qui a
    # déclenché cette sollicitation de l'assistant, pour lier sans ambiguïté
    # la réponse IA à la tentative concernée (cf. ai_interactions.progress_id).
    progress_id: int | None = None

class LogEvent(BaseModel):
    exercise_id: int
    status: str
    error_type: str | None = None
    session_id: str
    duration: int | None = None
    code: str | None = None

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
    weekly_practice_time: int

class WeeklyTrendPoint(BaseModel):
    week_start: str
    exercises_completed: int
    success_rate_no_ai: float
    ai_requests_per_attempt: float
    has_activity: bool

class StudentMetrics(BaseModel):
    progression: ProgressionMetrics
    autonomie: AutonomieMetrics
    qualite: QualiteMetrics
    engagement: EngagementMetrics
    trends: list[WeeklyTrendPoint] = []

class UserInfo(BaseModel):
    username: str
    nom: str | None = None
    prenom: str | None = None
    ai_enabled: bool = False
    role: str = "student"
    must_change_password: bool = False
    consent_given: bool = False
    ai_disabled: bool = False

class ConsentUpdate(BaseModel):
    consent_given: bool

class UserCreate(BaseModel):
    username: str
    nom: str | None = None
    prenom: str | None = None

class UserUpdate(BaseModel):
    username: str | None = None
    nom: str | None = None
    prenom: str | None = None
    ai_disabled: bool | None = None

class UserPasswordReset(BaseModel):
    username: str

class AdminCreate(BaseModel):
    username: str
    nom: str | None = None
    prenom: str | None = None
    etablissement: str | None = None
    email: str | None = None

class AdminUpdate(BaseModel):
    username: str
    nom: str | None = None
    prenom: str | None = None
    etablissement: str | None = None
    email: str | None = None

class AdminPasswordReset(BaseModel):
    admin_id: int

class AdminPasswordChange(BaseModel):
    current_password: str
    new_password: str

class LLMSettingsUpdate(BaseModel):
    llm_provider: str
    llm_model_openrouter: str
    llm_model_albert: str
    # None = ne pas modifier la clé enregistrée ; "" = supprimer la clé enregistrée
    # (retour à la variable d'environnement) ; valeur non vide = enregistrer cette clé (chiffrée).
    openrouter_api_key: str | None = None
    albert_api_key: str | None = None

class LLMSettingsOut(BaseModel):
    llm_provider: str
    llm_model_openrouter: str
    llm_model_albert: str
    openrouter_key_configured: bool = False
    albert_key_configured: bool = False
    openrouter_key_source: str | None = None
    albert_key_source: str | None = None
    openrouter_key_hint: str | None = None
    albert_key_hint: str | None = None

class AdminOut(BaseModel):
    id: int
    username: str
    nom: str = ""
    prenom: str = ""
    etablissement: str | None = None
    email: str | None = None
    is_super: bool
    must_change_password: bool = False
    nb_students: int = 0
    nb_exercises: int = 0
    nb_ai_requests: int = 0
    nb_total_requests: int = 0
    last_activity: str | None = None
