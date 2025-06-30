from fastapi import APIRouter
from pydantic import BaseModel
from app.graph.engine import run_graph_flow

router = APIRouter()

class QuestionInput(BaseModel):
    question: str

@router.post("/check-mode")
def classify_question(data: QuestionInput):
    result = run_graph_flow(data.question)
    return result  # trả về dict {"status": ..., "message": ...}
