from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.graph.nodes.classify_topic_node import check_mode

router = APIRouter()

class QuestionInput(BaseModel):
    question: str

@router.post("/check-mode")
def classify_question(data: QuestionInput):
    """
    Phân loại chủ đề câu hỏi
    """
    try:
        result = check_mode(data.question)
        return {
            "status": "success" if result == "yes" else "rejected",
            "message": "Câu hỏi thuộc chủ đề dinh dưỡng" if result == "yes" else "Câu hỏi không thuộc chủ đề dinh dưỡng",
            "classification": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi phân loại: {str(e)}")
