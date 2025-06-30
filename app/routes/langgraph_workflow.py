from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
import jwt
from app.graph.engine import run_langgraph_workflow
from app.config import JWT_SECRET_KEY

router = APIRouter()

class WorkflowInput(BaseModel):
    question: str  # Chỉ cần question, user_id sẽ lấy từ token

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
    user_id: str = Depends(get_user_id_from_token)
):
    """
    Xử lý câu hỏi sử dụng LangGraph workflow:
    1. Xác định user từ JWT token
    2. Phân loại chủ đề câu hỏi
    3. Tính BMI/BMR nếu cần
    4. Trả về kết quả hoàn chỉnh
    
    Headers:
    - Authorization: Bearer <JWT_TOKEN>
    
    Body:
    - question: Câu hỏi cần xử lý
    """
    try:
        # Chạy LangGraph workflow với user_id từ token
        result = run_langgraph_workflow(user_id, data.question)
        
        return result
        
    except Exception as e:
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
                "description": "Phân loại chủ đề câu hỏi sử dụng OpenAI GPT-4"
            },
            {
                "name": "calculate_bmi",
                "description": "Tính BMI, BMR và nhu cầu calo cho user"
            },
            {
                "name": "generate_result",
                "description": "Tạo kết quả cuối cùng"
            }
        ],
        "flow": [
            "identify_user → classify_topic → calculate_bmi → generate_result",
            "identify_user → classify_topic → end_rejected (nếu không thuộc chủ đề)",
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
            "body": {
                "question": "Câu hỏi cần xử lý"
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