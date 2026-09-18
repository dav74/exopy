from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from core.security import get_current_admin, AuthUser
from core.database import get_db
from datetime import datetime, timezone
import psycopg2.extras
import secrets
import csv
import io
import json
import zipfile

router = APIRouter(prefix="/api/research", tags=["research"])

PROGRESS_FIELD_KEYS = {
    "exercise_id", "exercise_titre", "niveau", "status", "error_type",
    "duration", "ai_used", "ai_disabled", "code", "ai_response",
}

# Champs exportés avant l'introduction du choix de champs : conservés comme
# valeur de repli si l'appelant n'envoie aucun `fields` (ex: ancien client,
# appel direct de l'API) pour ne pas produire un export quasi vide.
DEFAULT_FIELDS = {
    "exercise_id", "exercise_titre", "niveau", "status", "error_type",
    "duration", "ai_used",
}


def _ensure_pseudonyms(cur, admin_id: int, usernames: list[str]) -> dict[str, str]:
    cur.execute(
        "SELECT user_id, pseudo_id FROM research_pseudonyms WHERE admin_id = %s AND user_id = ANY(%s)",
        (admin_id, usernames)
    )
    pseudo_map = {r['user_id']: r['pseudo_id'] for r in cur.fetchall()}
    for uname in usernames:
        if uname in pseudo_map:
            continue
        pseudo = f"EL-{secrets.token_hex(4).upper()}"
        cur.execute(
            """INSERT INTO research_pseudonyms (user_id, pseudo_id, admin_id)
               VALUES (%s, %s, %s) ON CONFLICT (user_id) DO NOTHING""",
            (uname, pseudo, admin_id)
        )
        pseudo_map[uname] = pseudo
    return pseudo_map


def _build_ai_response_map(ai_rows: list[dict]) -> dict[int, str]:
    """Associe chaque tentative (par id user_progress) à la réponse de l'assistant
    obtenue pour elle, via le lien exact ai_interactions.progress_id transmis par
    le client au moment de la sollicitation (cf. RequestExercise.progress_id).

    Volontairement PAS de corrélation par déduction temporelle en repli : un appel
    LLM peut prendre plusieurs secondes, pendant lesquelles l'élève peut resoumettre
    du code, ce qui rendrait une déduction par horodatage ambiguë (risque de faux
    positif/négatif). Les échanges IA sans progress_id (données antérieures à
    l'introduction de ce lien) sont donc exclus plutôt que devinés."""
    response_map: dict[int, str] = {}
    for r in ai_rows:
        if r['progress_id'] is None:
            continue
        if r['progress_id'] in response_map:
            response_map[r['progress_id']] += " | " + r['ai_response']
        else:
            response_map[r['progress_id']] = r['ai_response']
    return response_map


def _build_progress_records(pseudo_map: dict[str, str], ai_disabled_map: dict[str, bool], progress_rows: list[dict], ai_response_map: dict[int, str], fields: set[str]) -> list[dict]:
    records = []
    for r in progress_rows:
        rec = {
            "pseudo_id": pseudo_map[r['user_id']],
            "date": r['created_at'].isoformat(),
        }
        if "exercise_id" in fields:
            rec["exercise_id"] = r['exercise_id']
        if "exercise_titre" in fields:
            rec["exercise_titre"] = r['titre']
        if "niveau" in fields:
            rec["niveau"] = r['niveau']
        if "status" in fields:
            rec["status"] = r['status']
        if "error_type" in fields:
            rec["error_type"] = r['error_type']
        if "duration" in fields:
            rec["duration"] = r['duration']
        if "ai_used" in fields:
            rec["ai_used"] = "yes" if ai_response_map.get(r['id']) else "no"
        if "ai_disabled" in fields:
            rec["ai_disabled"] = "yes" if ai_disabled_map.get(r['user_id']) else "no"
        if "code" in fields:
            rec["code"] = r['code']
        if "ai_response" in fields:
            rec["ai_response"] = ai_response_map.get(r['id'])
        records.append(rec)
    return records


def _build_data_dictionary(nb_students: int, fields: set[str]) -> str:
    lines = [
        "EXOPY - Export de recherche pseudonymisé",
        f"Généré le : {datetime.now(timezone.utc).isoformat()}",
        f"Élèves inclus (consentement valide et non révoqué) : {nb_students}",
        "",
        "progress_events.csv : une ligne par tentative de soumission (succès ou échec)",
        "  pseudo_id       - identifiant pseudonymisé stable dans le temps ; ne permet pas de",
        "                    retrouver l'élève sans la table de correspondance conservée par l'établissement",
        "  date            - date et heure exactes de l'événement (ISO 8601)",
    ]
    field_docs = {
        "exercise_id": "  exercise_id     - identifiant de l'exercice",
        "exercise_titre": "  exercise_titre  - titre de l'exercice",
        "niveau": "  niveau          - niveau de difficulté (1=très facile ... 4=expert)",
        "status": "  status          - success | failure",
        "error_type": "  error_type      - type d'erreur Python détecté (si échec)",
        "duration": "  duration        - durée en secondes depuis la dernière action sur cet exercice",
        "ai_used": "  ai_used         - yes | no : une réponse de l'assistant IA a été obtenue pour cette tentative",
        "ai_disabled": "  ai_disabled     - yes | no : l'assistant IA est-il désactivé pour cet élève par l'enseignant",
        "code": "  code            - code source proposé par l'élève pour cette tentative (texte brut)",
        "ai_response": "  ai_response     - réponse texte de l'assistant IA suite à cette tentative, si sollicité (texte brut)",
    }
    for key in ("exercise_id", "exercise_titre", "niveau", "status", "error_type", "duration", "ai_used", "ai_disabled", "code", "ai_response"):
        if key in fields:
            lines.append(field_docs[key])

    lines += [
        "",
        "Attention : cet export contient l'horodatage exact de chaque événement (plus de",
        "généralisation à la semaine). Le recoupement d'horaires précis avec l'emploi du temps",
        "d'un petit effectif d'élèves peut faciliter une ré-identification ; à garder en tête avant toute",
        "diffusion externe des données.",
    ]
    if "code" in fields or "ai_response" in fields:
        lines.append(
            "Attention : le texte brut (code et/ou réponses de l'assistant IA) est inclus dans cet export :"
            " à relire avant toute diffusion externe (peut contenir des noms en commentaire ou d'autres"
            " informations identifiantes)."
        )
    if "ai_used" in fields or "ai_response" in fields:
        lines.append(
            "Fiabilité ai_used/ai_response : ces deux champs reposent sur un lien exact entre la tentative"
            " et l'échange IA (établi au moment de la sollicitation), jamais sur une déduction par horodatage."
            " Les échanges IA antérieurs à l'introduction de ce lien exact n'ont pas pu être rattachés avec"
            " certitude à une tentative précise et sont donc absents de cet export plutôt que devinés :"
            " aucun risque de faux positif, un léger risque de sous-comptage pour les données les plus anciennes."
        )
    return "\n".join(lines) + "\n"


@router.get('/export')
def export_research_data(
    format: str = Query("csv", pattern="^(csv|json)$"),
    fields: list[str] = Query([]),
    admin: AuthUser = Depends(get_current_admin)
):
    admin_id = admin.admin_id
    selected_fields = set(fields) & PROGRESS_FIELD_KEYS
    if not selected_fields:
        selected_fields = set(DEFAULT_FIELDS)
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """SELECT u.username FROM users u
                       JOIN research_consent rc ON rc.user_id = u.username
                       WHERE u.admin_id = %s AND rc.consent_given = TRUE AND rc.revoked_at IS NULL""",
                    (admin_id,)
                )
                consenting = [r['username'] for r in cur.fetchall()]

                if not consenting:
                    raise HTTPException(status_code=400, detail="Aucun élève n'a de consentement recherche valide pour le moment.")

                pseudo_map = _ensure_pseudonyms(cur, admin_id, consenting)

                ai_disabled_map = {}
                if "ai_disabled" in selected_fields:
                    cur.execute(
                        "SELECT username, ai_disabled FROM users WHERE username = ANY(%s)",
                        (consenting,)
                    )
                    ai_disabled_map = {r['username']: r['ai_disabled'] for r in cur.fetchall()}

                cur.execute(
                    """SELECT up.id, up.user_id, up.exercise_id, up.session_id, e.titre, e.niveau, up.status,
                              up.error_type, up.duration, up.code, up.created_at
                       FROM user_progress up
                       JOIN exercises e ON e.id = up.exercise_id
                       WHERE up.user_id = ANY(%s) AND e.admin_id = %s AND up.status IN ('success', 'failure')
                       ORDER BY up.user_id, up.exercise_id, up.created_at""",
                    (consenting, admin_id)
                )
                progress_rows = cur.fetchall()

                # ai_used est dérivé du même lien exact que ai_response (progress_id, plutôt que
                # la colonne up.ai_used, mise à jour a posteriori par un appel réseau distinct côté
                # client, non rejoué en cas d'échec, et donc peu fiable) pour que les deux champs
                # restent toujours cohérents entre eux.
                ai_response_map = {}
                if "ai_response" in selected_fields or "ai_used" in selected_fields:
                    cur.execute(
                        """SELECT progress_id, ai_response
                           FROM ai_interactions
                           WHERE user_id = ANY(%s) AND progress_id IS NOT NULL""",
                        (consenting,)
                    )
                    ai_rows = cur.fetchall()
                    ai_response_map = _build_ai_response_map(ai_rows)

        progress_records = _build_progress_records(pseudo_map, ai_disabled_map, progress_rows, ai_response_map, selected_fields)

        data_dictionary = _build_data_dictionary(len(consenting), selected_fields)

        if format == "json":
            payload = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "nb_students": len(consenting),
                "progress_events": progress_records,
                "data_dictionary": data_dictionary
            }
            return Response(
                content=json.dumps(payload, indent=2, ensure_ascii=False),
                media_type="application/json",
                headers={"Content-Disposition": "attachment; filename=exopy_research_export.json"}
            )

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            s = io.StringIO()
            if progress_records:
                writer = csv.DictWriter(s, fieldnames=list(progress_records[0].keys()))
                writer.writeheader()
                writer.writerows(progress_records)
            zf.writestr("progress_events.csv", s.getvalue())
            zf.writestr("data_dictionary.txt", data_dictionary)
        buffer.seek(0)
        return Response(
            content=buffer.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=exopy_research_export.zip"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
