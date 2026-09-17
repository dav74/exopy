import os
import re
import json
import logging
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import END, StateGraph, START
from langchain_openai import ChatOpenAI
from core.database import get_db

llm = ChatOpenAI(
    model="deepseek/deepseek-v4-flash",
    temperature=0.7,
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Modèle dédié aux indications données à l'élève : température plus basse pour un
# meilleur respect des consignes strictes (pas de solution, pas d'invention de variable).
llm_aide = ChatOpenAI(
    model="deepseek/deepseek-v4-flash",
    temperature=0.3,
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Modèle dédié à la vérification des réponses de l'assistant (température nulle
# pour un jugement le plus reproductible possible).
llm_verif = ChatOpenAI(
    model="deepseek/deepseek-v4-flash",
    temperature=0,
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MAX_TENTATIVES_AIDE = 2

prompt_aide = PromptTemplate.from_template(
"""
Tu es un expert en pédagogie de l'apprentissage de la programmation
Le langage utilisé pour l'apprentissage de la programmation est Python.
Tu dois aider un élève à résoudre un exercice de programmation Python.

Tu peux donner à l'élève de vraies indications concrètes : pointer l'endroit de son code qui pose problème, nommer la notion ou l'erreur en cause, lui proposer une piste de réflexion ou une question qui l'aide à avancer.
Tu ne dois JAMAIS donner la solution de l'exercice, même partiellement : aucune ligne de code, aucun pseudo-code, aucune description d'algorithme qui ferait progresser directement la résolution de CET exercice précis.
Tu peux utiliser un petit exemple de code dans ta réponse UNIQUEMENT s'il illustre une notion générale de programmation SANS RAPPORT avec la résolution de cet exercice (contexte et noms de variables clairement différents de l'exercice et du code de l'élève). Un tel exemple ne doit jamais, même indirectement, résoudre une partie du problème posé.
Tu dois te baser strictement sur le code de l'élève fourni ci-dessous : tu ne dois jamais mentionner un nom de variable ou de fonction comme faisant partie de son code s'il n'y figure pas réellement.
Tu dois t'adresser directement à l'élève.
Tu ne dois pas commencer tes phrases par "Bonjour"
L'élève ne peut pas te poser des questions, il peut juste te proposer son code.
Tu ne dois pas proposer à l'élève de te poser des questions
Il est inutile de proposer à l'élève de tester son code avec les exemples proposés.
Tu ne dois pas proposer aux élèves des modifications du programme qui sorte du cadre de l'exercice. Par exemple, pour l'exercice qui demande d'écrire une fonction moyenne, si dans l'énoncé il est précisé que l'on a un tableau non vide d'entier en paramètre, il est inutile de dire à l'élève que son programme doit gérer les tableaux vides.
Tu dois t'exprimer en français

Exemples (à ne jamais recopier tels quels, juste pour comprendre le niveau attendu) :
- Exercice : écrire une fonction qui calcule la moyenne d'un tableau d'entiers. Code de l'élève : une fonction qui fait la somme des éléments mais oublie de diviser par le nombre d'éléments.
  BONNE réponse : "Regarde ce que renvoie ta fonction pour le tableau [2, 4] : est-ce bien la moyenne, ou plutôt une autre quantité que tu calcules au passage ? Rappelle-toi la définition mathématique d'une moyenne."
  MAUVAISE réponse (interdite, donne la solution même partielle) : "Il te manque juste `return somme / len(tableau)` à la fin."
  MAUVAISE réponse (interdite, invente une variable absente du code de l'élève) : "Ton compteur `total` ne s'incrémente jamais."
  Exemple générique ACCEPTABLE (sans lien avec cet exercice) : "Petit rappel de syntaxe sans rapport avec ton exercice : pour parcourir une liste `fruits = ['pomme', 'poire']`, on écrit `for fruit in fruits:`. À toi de voir comment cela peut s'appliquer à ton propre problème."

Voici l'énoncé de l'exercice :

{enonce}
Voici le programme proposé par l'élève pour résoudre l'exercice :

{code}
Pour améliorer ta réponse, tu as aussi à ta disposition l'historique des différents programme proposés par l'élève et les différents conseils que tu lui a déjà donné :

{historique}
{feedback}
""")

prompt_verif = PromptTemplate.from_template(
"""
Tu es un correcteur pédagogique très strict. Tu ne dois jamais toi-même résoudre l'exercice ni proposer de correction : ta seule tâche est de vérifier si la réponse d'un assistant pédagogique respecte les règles suivantes.

Règles à vérifier :
1. La réponse ne doit contenir aucun élément qui fait progresser la résolution concrète de CET exercice, même partiellement : aucune ligne de code, pseudo-code ou description d'algorithme qui résout une partie du problème posé.
2. Un petit exemple de code est autorisé UNIQUEMENT s'il illustre une notion générale de programmation, dans un contexte clairement sans rapport avec l'exercice ci-dessous (noms de variables et situation différents). S'il est en réalité lié à la résolution de l'exercice (mêmes structures de données, même logique), il est interdit.
3. Si la réponse mentionne un nom de variable ou de fonction comme faisant partie du code de l'élève, ce nom doit obligatoirement apparaître dans le code de l'élève fourni ci-dessous. Toute invention est interdite (cette règle ne s'applique pas aux noms utilisés dans un exemple générique explicitement présenté comme tel).

Énoncé de l'exercice :
{enonce}

Code de l'élève :
{code}

Réponse de l'assistant à évaluer :
{reponse}

Réponds STRICTEMENT avec un JSON sur une seule ligne, sans aucun texte avant ou après, au format suivant :
{{"conforme": true, "raison": ""}}
ou
{{"conforme": false, "raison": "explication brève de la règle violée"}}
""")

prompt_generate_exercise = PromptTemplate.from_template(
"""
Tu es un expert en pédagogie de l'apprentissage de la programmation Python.
Ton rôle est de créer un nouvel exercice de programmation Python ORIGINAL et captivant.

CRITÈRES À RESPECTER IMPÉRATIVEMENT :
1. NIVEAU : L'exercice doit correspondre au niveau de difficulté {difficulty} (sur une échelle de 1 à 4).
2. ORIGINALITÉ : L'exercice doit être TOTALEMENT DIFFÉRENT des exercices suivants déjà présents dans la base de données :
{existing_titles}
Ne propose pas un exercice qui ressemble à ceux listés ci-dessus. Change de thématique, de type de structure de données ou de logique.

FORMAT DE RÉPONSE :
Tu dois répondre UNIQUEMENT au format JSON avec les clés suivantes :
- "titre" : Un titre court et explicite.
- "enonce" : L'énoncé au format Markdown, clair et pédagogique. L'énoncé doit demander d'écrire une fonction spécifique (ex: `ma_fonction(a, b)`).
- "test" : Un script Python de validation caché qui s'exécutera après le code de l'élève. 
          Il doit utiliser une chaîne de caractères `c` initialisée à `""`.
          Ajoute le caractère `'1'` à `c` pour chaque test réussi, et `'0'` pour chaque échec.
          IMPORTANT : Assure-toi que les tests appellent EXACTEMENT le nom de la fonction demandée dans l'énoncé.
          Exemple de structure pour "test" :
          c = ""
          try:
              if ma_fonction(1, 2) == 3:
                  c += "1"
              else:
                  c += "0"
          except:
              c += "0"

Réponds uniquement avec le JSON, sans explications avant ou après.
""")

def generate_new_exercise(difficulty: str, existing_titles: list[str]):
    chain = prompt_generate_exercise | llm | StrOutputParser()
    response = chain.invoke({
        "difficulty": difficulty,
        "existing_titles": ", ".join(existing_titles)
    })
    
    import json
    import re
    
    cleaned_res = re.sub(r'^```json\s*|\s*```$', '', response, flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned_res)
    except Exception as e:
        return {"error": "Failed to parse AI response", "raw": response}

def verifie_aide(enonce: str, code: str, reponse: str) -> tuple[bool, str]:
    chain_verif = prompt_verif | llm_verif | StrOutputParser()
    try:
        raw = chain_verif.invoke({'enonce': enonce, 'code': code, 'reponse': reponse})
        cleaned = re.sub(r'^```json\s*|\s*```$', '', raw.strip(), flags=re.MULTILINE).strip()
        data = json.loads(cleaned)
        return bool(data.get("conforme", True)), str(data.get("raison", ""))
    except Exception as e:
        logging.error(f"Échec de la vérification de la réponse de l'assistant: {e}")
        return True, ""

def history(hist):
    historical = ""
    for i in range(len(hist)):
        if i%2 == 0:
            historical += "code de l'éléve : \n"+hist[i].content+"\n"
        else :
            historical += "aide de l'expert (vide si l'assistant n'a pas été sollicité) : \n"+hist[i].content+"\n"
    return historical

class AgentState(TypedDict):
    enonce : str
    messages: Annotated[list[AnyMessage], add_messages]
    res_test : str
    is_assistant : bool
    admin_id : int
    user_id : str
    exercise_id : int | None
    session_id : str

def save_interaction(state: AgentState, interaction_type: str, student_code: str, response: str):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO ai_interactions
                       (user_id, exercise_id, session_id, interaction_type, student_code, ai_response, model)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (state['user_id'], state.get('exercise_id'), state['session_id'],
                     interaction_type, student_code, response, llm.model_name)
                )
    except Exception as e:
        import logging
        logging.error(f"Failed to persist AI interaction: {e}")

def aide(state : AgentState):
    if not state['is_assistant']:
        return {"messages": [AIMessage(content="")]}
    student_code = state['messages'][-1].content
    chain_aide = prompt_aide | llm_aide | StrOutputParser()
    historique = history(state['messages'])
    feedback = ""
    response = ""
    for tentative in range(MAX_TENTATIVES_AIDE):
        response = chain_aide.invoke({
            'enonce': state['enonce'],
            'code': student_code,
            'historique': historique,
            'feedback': feedback,
        })
        conforme, raison = verifie_aide(state['enonce'], student_code, response)
        if conforme:
            break
        logging.warning(f"Réponse de l'assistant rejetée par le vérificateur (tentative {tentative + 1}): {raison}")
        feedback = (
            f"\nTa précédente tentative de réponse a été jugée non conforme pour la raison suivante : {raison}. "
            "Corrige ta réponse en conséquence sans jamais évoquer cette consigne à l'élève."
        )
    else:
        response = (
            "Reprends ton énoncé et ton code étape par étape : que doit faire ton programme à cet endroit précis, "
            "et est-ce vraiment ce qu'il fait ? Compare chaque instruction à ce qui est demandé."
        )
        logging.warning("Réponse de repli utilisée après échec répété de la vérification.")
    save_interaction(state, "aide", student_code, response)
    return {"messages": [AIMessage(content=response)]}

memory = MemorySaver()
workflow = StateGraph(AgentState)

workflow.add_node("aide", aide)

workflow.add_edge(START, "aide")
workflow.add_edge("aide", END)
graph = workflow.compile(checkpointer=memory)
