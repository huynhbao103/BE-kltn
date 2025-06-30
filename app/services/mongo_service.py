from app.config import mongo_db
from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

class MongoService:
    def __init__(self):
        self.db = mongo_db
        self.users_collection = self.db.users

    def _convert_to_object_id(self, user_id: str) -> ObjectId:
        """
        Chuyển đổi string ID thành ObjectId
        """
        try:
            return ObjectId(user_id)
        except Exception as e:
            print(f"Error converting to ObjectId: {e}")
            raise ValueError(f"Invalid ObjectId format: {user_id}")

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin user theo ID
        """
        try:
            object_id = self._convert_to_object_id(user_id)
            user = self.users_collection.find_one({"_id": object_id})
            if user:
                # Convert ObjectId to string for JSON serialization
                user["_id"] = str(user["_id"])
            return user
        except Exception as e:
            print(f"Error getting user: {e}")
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin user theo email
        """
        try:
            user = self.users_collection.find_one({"email": email})
            if user:
                user["_id"] = str(user["_id"])
            return user
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None

    def create_user(self, user_data: Dict[str, Any]) -> Optional[str]:
        """
        Tạo user mới
        """
        try:
            result = self.users_collection.insert_one(user_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating user: {e}")
            return None

    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Cập nhật thông tin user
        """
        try:
            result = self.users_collection.update_one(
                {"_id": user_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating user: {e}")
            return False

    def get_user_health_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Lấy dữ liệu sức khỏe của user theo schema Next.js
        """
        try:
            object_id = self._convert_to_object_id(user_id)
            user = self.users_collection.find_one(
                {"_id": object_id},
                {
                    "name": 1,
                    "email": 1,
                    "dateOfBirth": 1,
                    "gender": 1,
                    "weight": 1,
                    "height": 1,
                    "activityLevel": 1,
                    "medicalConditions": 1,
                    "lastUpdateDate": 1
                }
            )
            
            if not user:
                print(f"User not found with ID: {user_id}")
                return None
                
            # Convert ObjectId to string
            user["_id"] = str(user["_id"])
            
            # Tính tuổi từ dateOfBirth
            if user.get("dateOfBirth"):
                birth_date = user["dateOfBirth"]
                if isinstance(birth_date, str):
                    birth_date = datetime.fromisoformat(birth_date.replace('Z', '+00:00'))
                elif isinstance(birth_date, datetime):
                    pass
                else:
                    birth_date = datetime.fromisoformat(str(birth_date))
                
                today = datetime.now()
                age = today.year - birth_date.year
                if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                    age -= 1
                user["age"] = age
            else:
                user["age"] = None
                print(f"Warning: No dateOfBirth for user {user_id}")
            
            # Sử dụng trực tiếp activityLevel string
            user["activity_level"] = user.get("activityLevel", "sedentary")
            
            # Kiểm tra dữ liệu cần thiết
            missing_fields = []
            if not user.get("weight"):
                missing_fields.append("weight")
            if not user.get("height"):
                missing_fields.append("height")
            if not user.get("age"):
                missing_fields.append("age (from dateOfBirth)")
            
            if missing_fields:
                print(f"Missing required fields for user {user_id}: {missing_fields}")
            
            return user
        except Exception as e:
            print(f"Error getting user health data: {e}")
            return None

    def update_user_health_data(self, user_id: str, health_data: Dict[str, Any]) -> bool:
        """
        Cập nhật dữ liệu sức khỏe của user
        """
        try:
            object_id = self._convert_to_object_id(user_id)
            # Thêm lastUpdateDate
            health_data["lastUpdateDate"] = datetime.now()
            
            result = self.users_collection.update_one(
                {"_id": object_id},
                {"$set": health_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating user health data: {e}")
            return False

    def save_bmi_calculation(self, user_id: str, bmi_data: Dict[str, Any]) -> bool:
        """
        Lưu kết quả tính BMI vào user profile
        """
        try:
            object_id = self._convert_to_object_id(user_id)
            update_data = {
                "bmi": bmi_data.get("bmi"),
                "bmi_category": bmi_data.get("bmi_category"),
                "bmr": bmi_data.get("bmr"),
                "calorie_need_per_day": bmi_data.get("calorie_need_per_day"),
                "last_bmi_calculation": bmi_data,
                "lastUpdateDate": datetime.now()
            }
            
            result = self.users_collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error saving BMI calculation: {e}")
            return False

# Tạo instance global
mongo_service = MongoService() 