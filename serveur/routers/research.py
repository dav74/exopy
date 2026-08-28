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


def _attribute_ai_requests(pseudo_map: dict[str, str], progress_rows: list[dict]) -> list[dict]:
    groups: dict[tuple, list[dict]] = {}
    for r in progress_rows:
        groups.setdefault((r['user_id'], r['exercise_id']), []).append(r)

    records = []
    for (user_id, exercise_id), rows in groups.items():
        rows.sort(key=lambda r: r['created_at'])
        pending = None
        for r in rows:
            if r['status'] in ('success', 'failure'):
                if pending is not None:
                    records.append(pending)
                pending = {
                    "pseudo_id": pseudo_map[user_id],
                    "exercise_id": exercise_id,
                    "exercise_titre": r['titre'],
                    "niveau": r['niveau'],
                    "status": r['status'],
                    "error_type": r['error_type'],
                    "duration": r['duration'],
                    "ai_request": "no",
                    "date": r['created_at'].isoformat()
                }
            elif r['status'] == 'ai_request' and pending is not None:
                pending["ai_request"] = "yes"
        if pending is not None:
            records.append(pending)
    return records


def _build_data_dictionary(nb_students: int, include_raw_text: bool) -> str:
    lines = [
        "EXOPY - Export de recherche pseudonymisé",
        f"Généré le : {datetime.now(timezone.utc).isoformat()}",
        f"Élèves inclus (consentement valide et non révoqué) : {nb_students}",
        "",
        "progress_events.csv :",
        "  pseudo_id       - identifiant pseudonymisé stable dans le temps ; ne permet pas de",
        "                    retrouver l'élève sans la table de correspondance conservée par l'établissement",
        "  exercise_id     - identifiant de l'exercice",
        "  exercise_titre  - titre de l'exercice",
        "  niveau          - niveau de difficulté (1=très facile ... 4=expert)",
        "  status          - success | failure (une ligne par tentative de soumission)",
        "  ai_request      - yes | no : l'assistant IA a-t-il été sollicité pour cette tentative",
        "  error_type      - type d'erreur Python détecté (si échec)",
        "  duration        - durée en secondes depuis la dernière action sur cet exercice",
        "  date            - date et heure exactes de l'événement (ISO 8601)",
        "",
        "ai_interactions.csv :",
        "  pseudo_id         - identifiant pseudonymisé",
        "  exercise_id       - exercice concerné",
        "  session_id        - identifiant de session (relie une série d'échanges sur un même exercice)",
        "  interaction_type  - aide (pendant l'exercice) | bilan (après réussite)",
        "  model             - modèle LLM utilisé",
        "  date              - date et heure exactes de l'échange (ISO 8601)",
        "",
        "Attention : cet export contient l'horodatage exact de chaque événement (plus de",
        "généralisation à la semaine). Le recoupement d'horaires précis avec l'emploi du temps",
        "d'un petit effectif d'élèves peut faciliter une ré-identification ; à garder en tête avant toute",
        "diffusion externe des données.",
    ]
    if include_raw_text:
        lines.append(
            "  student_code, ai_response - texte brut inclus : à relire avant toute diffusion externe"
            " (peut contenir des noms en commentaire)"
        )
    return "\n".join(lines) + "\n"


@router.get('/export')
def export_research_data(
    format: str = Query("csv", pattern="^(csv|json)$"),
    include_raw_text: bool = Query(False),
    admin: AuthUser = Depends(get_current_admin)
):
    admin_id = admin.admin_id
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

                cur.execute(
                    """SELECT up.user_id, up.exercise_id, e.titre, e.niveau, up.status, up.error_type,
                              up.duration, up.created_at
                       FROM user_progress up
                       JOIN exercises e ON e.id = up.exercise_id
                       WHERE up.user_id = ANY(%s) AND e.admin_id = %s
                       ORDER BY up.user_id, up.exercise_id, up.created_at""",
                    (consenting, admin_id)
                )
                progress_rows = cur.fetchall()

                ai_cols = "user_id, exercise_id, session_id, interaction_type, model, created_at"
                if include_raw_text:
                    ai_cols += ", student_code, ai_response"
                cur.execute(
                    f"""SELECT {ai_cols} FROM ai_interactions
                        WHERE user_id = ANY(%s)
                        ORDER BY user_id, created_at""",
                    (consenting,)
                )
                ai_rows = cur.fetchall()

        progress_records = _attribute_ai_requests(pseudo_map, progress_rows)

        ai_records = []
        for r in ai_rows:
            rec = {
                "pseudo_id": pseudo_map[r['user_id']],
                "exercise_id": r['exercise_id'],
                "session_id": r['session_id'],
                "interaction_type": r['interaction_type'],
                "model": r['model'],
                "date": r['created_at'].isoformat()
            }
            if include_raw_text:
                rec["student_code"] = r.get('student_code')
                rec["ai_response"] = r.get('ai_response')
            ai_records.append(rec)

        data_dictionary = _build_data_dictionary(len(consenting), include_raw_text)

        if format == "json":
            payload = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "nb_students": len(consenting),
                "progress_events": progress_records,
                "ai_interactions": ai_records,
                "data_dictionary": data_dictionary
            }
            return Response(
                content=json.dumps(payload, indent=2, ensure_ascii=False),
                media_type="application/json",
                headers={"Content-Disposition": "attachment; filename=exopy_research_export.json"}
            )

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, records in (("progress_events.csv", progress_records), ("ai_interactions.csv", ai_records)):
                s = io.StringIO()
                if records:
                    writer = csv.DictWriter(s, fieldnames=list(records[0].keys()))
                    writer.writeheader()
                    writer.writerows(records)
                zf.writestr(name, s.getvalue())
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
