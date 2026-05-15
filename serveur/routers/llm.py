from fastapi import APIRouter, Depends
import logging
from core.security import get_current_user
from models.schemas import RequestExercise
from services.llm import graph

router = APIRouter(tags=["llm"])

@router.post('/request')
def request_llm(req: RequestExercise, current_user: str = Depends(get_current_user)):
    config = {"configurable": {"thread_id": req.session}}
    rep = graph.invoke(
        {
            "enonce": req.enonce,
            "messages": req.code,
            "res_test": req.res_test,
            "is_assistant": req.is_assistant
        }, 
        config, 
        stream_mode="values"
    )
    logging.info(rep['messages'][-1].content)
    return {"response": rep['messages'][-1].content}
