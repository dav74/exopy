import os
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
import psycopg2.extras

llm = ChatOpenAI(
    model="deepseek/deepseek-v4-flash",
    temperature=0.7,
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

prompt_aide = PromptTemplate.from_template(
"""
Tu es un expert en pédagogie de l'apprentissage de la programmation
Le langage utilisé pour l'apprentissage de la programmation est Python.
Tu dois aider un élève à résoudre un exercice de programmation Python.
Tu ne dois jamais donner la solution de l'exercice (même partiellement) à l'élève, juste lui donner des inddications lui permettant de résoudre lui même l'exercice
Tu dois t'adresser directement à l'élève.
Tu ne dois pas commencer tes phrases par "Bonjour"
L'élève ne peut pas te poser des questions, il peut juste te proposer son code.
Tu ne dois pas proposer à l'élève de te poser des questions
Il est inutile de proposer à l'élève de tester son code avec les exemples proposés.
Tu ne dois pas proposer aux élèves des modifications du programme qui sorte du cadre de l'exercice. Par exemple, pour l'exercice qui demande d'écrire une fonction moyenne, si dans l'énoncé il est précisé que l'on a un tableau non vide d'entier en paramètre, il est inutile de dire à l'élève que son programme doit gérer les tableaux vides.
Tu dois t'exprimer en français
Voici l'énoncé de l'exercice :

{enonce}
Voici le programme proposé par l'élève pour résoudre l'exercice :

{code}
Pour améliorer ta réponse, tu as aussi à ta disposition l'historique des différents programme proposés par l'élève et les différents conseils que tu lui a déjà donné :

{historique} 
""")

prompt_bilan = PromptTemplate.from_template(
"""
Tu es un expert en pédagogie de l'apprentissage de la programmation
Le langage utilisé pour l'apprentissage de la programmation est Python.
Ton rôle est de proposer un bilan sur la résolution d'un exercice réaliser par un élève.
Tu dois t'adresser directement à l'élève.
Cet élève vient de réussir l'exercice suivant :

{enonce}
Voici l'historique de la résolution de cet exercice (code de l'élève et conseil donnés par un expert): 

{historique}
Tu dois faire un bilan sur les points forts de l'élève et les points à travailler
Ton bilan doit absolument être cohérent. Il vaut mieux ne rien mettre que de mettre une information inutile  
Tu dois proposer à l'élève un autre  exercice à résoudre parmi les exercices ci-dessous (pour chaque exercice tu as le titre de l'exercice, une liste de mots clé et un niveau allant de 1 à 4 (le niveau 1 étant le plus facile et le niveau 4 le plus difficile)) :
Tu ne dois UNIQUEMENT proposer un exercice appartenant à la liste ci-dessous.
Tu dois donner uniquement le titre et le numéro de l'exercice que tu proposes à l'élèves (inutile d'indiquer les mots clé liés à l'exercice)
Tu ne dois pas proposer l'exercice qui vient d'être résolu sauf si tu considères que l'élève n'a pas respecté les consignes données dans l'énoncé, à ce moment, tu dois lui demander de refaire l'exercice.
Quand l'élève a réussi un exercice tu dois lui proposer un exercice plus difficile (avec un niveau supérieur)
### LISTE DES EXERCICES 

{mot_cle}
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

def get_descr_exo(admin_id: int):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, titre, mots_cle, niveau FROM exercises WHERE admin_id = %s ORDER BY ordering, id",
                    (admin_id,)
                )
                rows = cur.fetchall()
        descr_exo = ""
        for row in rows:
            descr_exo += f"Exercice n° {row['id']} => titre : {row['titre'].replace(chr(10), '')} ; mots clé : {row['mots_cle'].replace(chr(10), '')} ; niveau : {row['niveau']}\n"
        return descr_exo
    except Exception:
        return ""

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

def routeur(state : AgentState):
    if state['res_test'] == "1" or state['res_test'] == "0":
        return "aide"
    else :
        return "bilan"

def aide(state : AgentState):
    if not state['is_assistant']:
        return {"messages": [AIMessage(content="")]}
    llm_aide = prompt_aide | llm | StrOutputParser()
    response = llm_aide.invoke({'enonce': state['enonce'], 'code' : state['messages'][-1].content, 'historique' : history(state['messages'])})
    return {"messages": [AIMessage(content=response)]}

def bilan(state : AgentState):
    llm_bilan = prompt_bilan | llm | StrOutputParser()
    descr_exo = get_descr_exo(state['admin_id'])
    response = llm_bilan.invoke({'enonce': state['enonce'], 'historique' : history(state['messages']), 'mot_cle': descr_exo})
    return {"messages": [AIMessage(content=response)]}

memory = MemorySaver()
workflow = StateGraph(AgentState)

workflow.add_node("aide", aide)
workflow.add_node("bilan", bilan)

workflow.add_conditional_edges(
    START,
    routeur,
    {
        "aide": "aide",
        "bilan": "bilan"
    })
workflow.add_edge("aide", END)
workflow.add_edge("bilan", END)
graph = workflow.compile(checkpointer=memory)
