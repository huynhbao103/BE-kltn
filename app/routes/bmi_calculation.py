from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.graph.nodes.calculate_bmi_node import calculate_bmi, calculate_bmi_from_user_id
from app.services.mongo_service import mongo_service
from app.config import mongo_client, mongo_db

router = APIRouter()

class UserHealthData(BaseModel):
    weight: float
    height: float
    dateOfBirth: Optional[str] = None
    gender: str = "male"
    activityLevel: str = "sedentary"
    name: Optional[str] = None
    email: Optional[str] = None

class UserIdInput(BaseModel):
    user_id: str


# @router.get("/list-users")
# def list_users():
#     """
#     Liệt kê tất cả users trong database (chỉ để test)
#     """
#     try:
#         users = list(mongo_db.users.find({}, {
#             "name": 1,
#             "email": 1,
#             "dateOfBirth": 1,
#             "weight": 1,
#             "height": 1,
#             "activityLevel": 1
#         }).limit(10))
        
#         # Convert ObjectId to string
#         for user in users:
#             user["_id"] = str(user["_id"])
        
#         return {
#             "total_users": len(users),
#             "users": users
#         }
#     except Exception as e:
#         raise HTTPException(
#             status_code=500, 
#             detail=f"Lỗi lấy danh sách users: {str(e)}"
#         )

# @router.get("/test-connection")
# def test_mongodb_connection():
#     """
#     Test kết nối MongoDB và kiểm tra database
#     """
#     try:
#         # Test kết nối cơ bản
#         mongo_client.admin.command('ping')
        
#         # Test truy cập database
#         db_list = mongo_client.list_database_names()
        
#         # Test truy cập collection users
#         users_count = mongo_db.users.count_documents({})
        
#         # Lấy sample user để kiểm tra
#         sample_user = mongo_db.users.find_one({})
#         sample_user_id = str(sample_user["_id"]) if sample_user else None
        
#         return {
#             "status": "success",
#             "message": "Kết nối MongoDB thành công!",
#             "database_name": mongo_db.name,
#             "available_databases": db_list,
#             "users_collection_count": users_count,
#             "sample_user_id": sample_user_id,
#             "connection_string": str(mongo_client.address)
#         }
#     except Exception as e:
#         raise HTTPException(
#             status_code=500, 
#             detail=f"Lỗi kết nối MongoDB: {str(e)}"
#         )

# @router.post("/calculate-bmi")
# def calculate_bmi_endpoint(data: UserHealthData):
#     """
#     Tính BMI và BMR với dữ liệu được cung cấp trực tiếp
#     """
#     try:
#         user_data = data.dict()
#         user_data["activity_level"] = data.activityLevel
        
#         # Tính tuổi từ dateOfBirth nếu có
#         if data.dateOfBirth:
#             from datetime import datetime
#             try:
#                 birth_date = datetime.fromisoformat(data.dateOfBirth.replace('Z', '+00:00'))
#                 today = datetime.now()
#                 age = today.year - birth_date.year
#                 if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
#                     age -= 1
#                 user_data["age"] = age
#             except:
#                 return {"error": "Định dạng ngày sinh không hợp lệ"}
#         else:
#             return {"error": "Cần cung cấp ngày sinh để tính tuổi"}
        
#         result = calculate_bmi(user_data)
#         if "error" in result:
#             raise HTTPException(status_code=400, detail=result["error"])
#         return result
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Lỗi tính toán: {str(e)}")

@router.post("/calculate")
def calculate_bmi_simple(data: UserIdInput):
    """
    Tính BMI đơn giản từ user_id
    """
    try:
        print(f"🔍 Calculating BMI for user: {data.user_id}")
        
        # Tính BMI trực tiếp
        result = calculate_bmi_from_user_id(data.user_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        # Trả về kết quả đơn giản
        return {
            "status": "success",
            "user_id": data.user_id,
            "bmi": result.get("bmi"),
            "bmi_category": result.get("bmi_category"),
            "user_info": {
                "name": result.get("user_info", {}).get("name"),
                "age": result.get("user_info", {}).get("age"),
                "weight": result.get("user_info", {}).get("weight"),
                "height": result.get("user_info", {}).get("height"),
                "medical_conditions": result.get("user_info", {}).get("medical_conditions", [])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tính BMI: {str(e)}")

@router.get("/user/{user_id}")
def get_user_bmi(user_id: str):
    """
    Lấy BMI của user theo user_id
    """
    try:
        result = calculate_bmi_from_user_id(user_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return {
            "status": "success",
            "user_id": user_id,
            "bmi": result.get("bmi"),
            "bmi_category": result.get("bmi_category"),
            "medical_conditions": result.get("user_info", {}).get("medical_conditions", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy BMI: {str(e)}")

# @router.get("/user/{user_id}")
# def get_user_health_data(user_id: str):
#     """
#     Lấy thông tin sức khỏe của user từ MongoDB
#     """
#     try:
#         user_data = mongo_service.get_user_health_data(user_id)
#         if not user_data:
#             raise HTTPException(status_code=404, detail="Không tìm thấy user")
#         return user_data
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Lỗi lấy dữ liệu: {str(e)}")
