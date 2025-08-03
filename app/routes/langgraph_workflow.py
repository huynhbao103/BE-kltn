from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, List
import jwt
from app.graph.engine import (
    run_langgraph_workflow_until_selection, 
    continue_workflow_with_cooking_method
)
from app.config import JWT_SECRET_KEY

router = APIRouter()

class WorkflowInput(BaseModel):
    question: str
    weather: Optional[str] = None
    time_of_day: Optional[str] = None
    session_id: Optional[str] = None
    ignore_context_filter: bool = False

class CookingMethodInput(BaseModel):
    session_id: str
    cooking_methods: List[str]
def get_user_id_from_token(authorization: Optional[str] = Header(None)) -> str:
    """
    Lấy user_id từ JWT token trong Authorization header
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required"
        )
    
    try:
        # Kiểm tra format "Bearer <token>"
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization format. Use 'Bearer <token>'"
            )
        
        token = authorization.split(" ")[1]
        
        # Decode JWT token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Token không chứa user_id"
            )
        
        return user_id
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token đã hết hạn"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Token không hợp lệ"
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Lỗi xác thực token: {str(e)}"
        )

@router.post("/process")
def process_with_langgraph(
    data: WorkflowInput,
    user_id: str = Depends(get_user_id_from_token),
):
    # Nếu không ignore context filter thì bắt buộc phải có weather và time_of_day
    if not data.ignore_context_filter:
        if not data.weather or not data.time_of_day:
            raise HTTPException(
                status_code=422,
                detail="weather và time_of_day là bắt buộc khi ignore_context_filter=False"
            )
    try:
        # Chạy workflow từ đầu để lấy phân tích và prompts
        result = run_langgraph_workflow_until_selection(
            user_id, data.question, data.weather, data.time_of_day, data.session_id, data.ignore_context_filter
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Lỗi xử lý workflow: {str(e)}"
        )

@router.post("/process-cooking")
def process_cooking_method(
    data: CookingMethodInput,
    user_id: str = Depends(get_user_id_from_token)
):
    """
    Nhận phương pháp chế biến, trả về kết quả cuối cùng.
    """
    try:
        result = continue_workflow_with_cooking_method(
            session_id=data.session_id,
            cooking_methods=data.cooking_methods,
            user_id=user_id
        )
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Lỗi xử lý workflow: {str(e)}"
        )





@router.get("/workflow-info")
def get_workflow_info():
    """
    Lấy thông tin về workflow
    """
    return {
        "workflow_name": "Nutrition Assistant Workflow",
        "description": "LangGraph workflow cho hệ thống tư vấn dinh dưỡng",
        "nodes": [
            {
                "name": "identify_user",
                "description": "Xác định user từ JWT token và lấy thông tin từ MongoDB"
            },
            {
                "name": "classify_topic", 
                "description": "Phân loại chủ đề câu hỏi sử dụng OpenAI GPT-4o"
            },
            {
                "name": "classify_intent",
                "description": "Phân tích intent của người dùng dựa trên session hiện có"
            },
            {
                "name": "select_emotion",
                "description": "Yêu cầu người dùng chọn cảm xúc hiện tại"
            },
            {
                "name": "select_cooking_method",
                "description": "Yêu cầu người dùng chọn phương pháp nấu"
            },
            {
                "name": "calculate_bmi",
                "description": "Tính BMI, BMR và nhu cầu calo cho user"
            },
            {
                "name": "query_neo4j",
                "description": "Truy vấn Neo4j để tìm thực phẩm phù hợp"
            },
            {
                "name": "aggregate_foods",
                "description": "Tổng hợp các món ăn phù hợp theo tiêu chí"
            },
            {
                "name": "rerank_foods",
                "description": "Sắp xếp lại thực phẩm theo mức độ phù hợp"
            },
            {
                "name": "generate_result",
                "description": "Tạo kết quả cuối cùng"
            }
        ],
        "flow": [
            "identify_user → classify_topic → classify_intent → select_emotion/select_cooking_method/calculate_bmi → ... → generate_result",
            "identify_user → classify_topic → end_rejected (nếu không thuộc chủ đề)",
            "classify_intent → select_emotion (nếu muốn thay đổi cảm xúc)",
            "classify_intent → select_cooking_method (nếu muốn thay đổi cách chế biến)",
            "classify_intent → calculate_bmi (nếu tiếp tục với lựa chọn hiện tại)",
            "Any node → end_with_error (nếu có lỗi)"
        ],
        "authentication": {
            "method": "JWT Token",
            "header": "Authorization: Bearer <token>",
            "note": "Token phải chứa user_id"
        },
        "usage": {
            "headers": {
                "Authorization": "Bearer <JWT_TOKEN>"
            },
            "endpoints": {
                "/process": {
                    "method": "POST",
                    "description": "Bắt đầu workflow và có thể yêu cầu chọn cảm xúc/chế độ ăn/phương pháp nấu",
                    "body": {
                        "question": "Câu hỏi cần xử lý"
                    }
                },
                "/process-emotion": {
                    "method": "POST", 
                    "description": "Tiếp tục workflow sau khi chọn cảm xúc",
                    "body": {
                        "session_id": "ID session từ response trước",
                        "emotion": "Cảm xúc đã chọn"
                    }
                },

                "/process-cooking-method": {
                    "method": "POST",
                    "description": "Tiếp tục workflow sau khi chọn phương pháp nấu",
                    "body": {
                        "session_id": "ID session từ response trước",
                        "cooking_methods": ["Luộc", "Xào", "Nướng"]
                    }
                },
                "/process-emotion-cooking": {
                    "method": "POST",
                    "description": "Nhận cảm xúc và phương pháp chế biến cùng lúc, trả về kết quả cuối cùng",
                    "body": {
                        "session_id": "ID session từ response trước",
                        "emotion": "Cảm xúc đã chọn",
                        "cooking_methods": ["Luộc", "Xào", "Nướng"]
                    }
                },
                "/classify-intent": {
                    "method": "POST",
                    "description": "Phân tích intent của người dùng dựa trên session hiện có",
                    "body": {
                        "session_id": "ID session từ response trước",
                        "question": "Câu hỏi mới của người dùng"
                    },
                    "response": {
                        "intent": "continue/change_emotion/change_cooking/change_both/restart",
                        "confidence": "high/medium/low",
                        "reasoning": "Lý do phân tích",
                        "suggested_emotion": "Cảm xúc đề xuất (nếu có)",
                        "suggested_cooking_methods": ["Cách chế biến đề xuất (nếu có)"],
                        "next_action": "Hành động tiếp theo"
                    }
                }
            },
            "example": {
                "headers": {
                    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                },
                "body": {
                    "question": "Tôi nên ăn gì để giảm cân?"
                }
            }
        }
    } 