from app.services.mongo_service import mongo_service
from typing import Dict, Any, Optional

def calculate_bmi_from_user_id(userId: str) -> Dict[str, Any]:
    """
    Tính BMI và BMR cho user dựa trên user_id từ MongoDB
    """
    # Lấy dữ liệu user từ MongoDB
    user_data: Optional[Dict[str, Any]] = mongo_service.get_user_health_data(userId)
    
    if not user_data:
        return {"error": "Không tìm thấy thông tin user"}
    
    # Kiểm tra dữ liệu cần thiết
    if not user_data.get("weight") or not user_data.get("height") or not user_data.get("age"):
        return {"error": "Thiếu thông tin cần thiết (cân nặng, chiều cao, hoặc ngày sinh)"}
    
    return calculate_bmi(user_data)

def calculate_bmi(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tính BMI cho người lớn và trẻ em (dưới 20 tuổi).
    """
    weight = user_data.get("weight")
    height = user_data.get("height")
    age = user_data.get("age")
    gender = user_data.get("gender", "male").lower()
    activity_level = user_data.get("activity_level", "sedentary")

    if not all([weight, height, age]):
        return {"error": "Thiếu dữ liệu cần thiết để tính toán."}

    # Tính BMI
    height_m = height / 100
    bmi = weight / (height_m ** 2)

    # Trẻ em (< 20 tuổi)
    if age < 20:
        if bmi < 14:
            bmi_category = "Thiếu cân (theo ước lượng)"
        elif 14 <= bmi < 20:
            bmi_category = "Bình thường (theo ước lượng)"
        elif 20 <= bmi < 22:
            bmi_category = "Thừa cân (theo ước lượng)"
        else:
            bmi_category = "Béo phì (theo ước lượng)"
    else:
        # Người lớn ≥ 20 tuổi
        if bmi < 18.5:
            bmi_category = "Gầy"
        elif 18.5 <= bmi < 24.9:
            bmi_category = "Bình thường"
        elif 25 <= bmi < 29.9:
            bmi_category = "Thừa cân"
        else:
            bmi_category = "Béo phì"

    result: Dict[str, Any] = {
        "bmi": round(bmi, 2),
        "bmi_category": bmi_category,
        "user_info": {
            "name": user_data.get("name", "Unknown"),
            "age": age,
            "gender": gender,
            "weight": weight,
            "height": height,
            "activity_level": activity_level,
            "medical_conditions": user_data.get("medicalConditions", [])
        }
    }
    
    # Lưu kết quả BMI vào MongoDB
    try:
        user_id = user_data.get("_id")
        if user_id:
            mongo_service.save_bmi_calculation(user_id, result)
    except Exception as e:
        print(f"Error saving BMI result to MongoDB: {e}")
    
    return result
