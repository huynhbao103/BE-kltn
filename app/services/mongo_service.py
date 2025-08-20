from app.config import mongo_db
from typing import Optional, Dict, Any, List
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
            object_id = self._convert_to_object_id(user_id)
            result = self.users_collection.update_one(
                {"_id": object_id},
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
                    "allergies": 1,
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

    def get_all_users(self) -> list:
        """
        Lấy tất cả users (cho mục đích test)
        """
        try:
            users = list(self.users_collection.find({}))
            # Convert ObjectId to string for each user
            for user in users:
                user["_id"] = str(user["_id"])
            return users
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []

    # ===== DISH MANAGEMENT =====
    
    def get_dishes_collection(self):
        """Lấy collection dishes"""
        return self.db.dishes
    
    def create_dish(self, dish_data: Dict[str, Any]) -> Optional[str]:
        """
        Tạo món ăn mới
        """
        try:
            dishes_collection = self.get_dishes_collection()
            result = dishes_collection.insert_one(dish_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating dish: {e}")
            return None
    
    def get_dish_by_id(self, dish_id: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin món ăn theo ID
        """
        try:
            dishes_collection = self.get_dishes_collection()
            dish = dishes_collection.find_one({"_id": dish_id})
            if dish:
                dish["_id"] = str(dish["_id"])
            return dish
        except Exception as e:
            print(f"Error getting dish: {e}")
            return None
    
    def get_all_dishes(self) -> List[Dict[str, Any]]:
        """
        Lấy tất cả món ăn
        """
        try:
            dishes_collection = self.get_dishes_collection()
            dishes = list(dishes_collection.find({}))
            for dish in dishes:
                dish["_id"] = str(dish["_id"])
            return dishes
        except Exception as e:
            print(f"Error getting all dishes: {e}")
            return []
    
    def filter_dishes_by_allergies(self, dishes: List[Dict[str, Any]], user_allergies: List[str]) -> List[Dict[str, Any]]:
        """
        Lọc món ăn theo danh sách dị ứng của user
        """
        if not user_allergies:
            return dishes
        
        filtered_dishes = []
        for dish in dishes:
            dish_ingredients = dish.get("ingredients", [])
            
            # Kiểm tra xem món ăn có chứa nguyên liệu dị ứng không
            has_allergic_ingredient = False
            for allergy in user_allergies:
                if allergy.lower() in [ing.lower() for ing in dish_ingredients]:
                    has_allergic_ingredient = True
                    break
            
            # Chỉ thêm món ăn không chứa nguyên liệu dị ứng
            if not has_allergic_ingredient:
                filtered_dishes.append(dish)
        
        return filtered_dishes
    
    def get_dishes_by_ids(self, dish_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Lấy danh sách món ăn theo danh sách ID
        """
        try:
            dishes_collection = self.get_dishes_collection()
            dishes = list(dishes_collection.find({"_id": {"$in": dish_ids}}))
            for dish in dishes:
                dish["_id"] = str(dish["_id"])
            return dishes
        except Exception as e:
            print(f"Error getting dishes by IDs: {e}")
            return []
    
    def update_dish(self, dish_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Cập nhật thông tin món ăn
        """
        try:
            dishes_collection = self.get_dishes_collection()
            result = dishes_collection.update_one(
                {"_id": dish_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating dish: {e}")
            return False
    
    def delete_dish(self, dish_id: str) -> bool:
        """
        Xóa món ăn
        """
        try:
            dishes_collection = self.get_dishes_collection()
            result = dishes_collection.delete_one({"_id": dish_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting dish: {e}")
            return False

    def get_cook_methods_by_ingredients(self, ingredients: List[str]) -> List[str]:
        """
        Lấy danh sách các phương pháp chế biến duy nhất từ các món ăn
        chứa một trong các nguyên liệu được cung cấp.
        """
        if not ingredients:
            return []
        try:
            dishes_collection = self.get_dishes_collection()
            pipeline = [
                {
                    "$match": {
                        "ingredients": {"$in": ingredients}
                    }
                },
                {
                    "$group": {
                        "_id": "$cook_method"
                    }
                },
                {
                    "$project": {
                        "cook_method": "$_id",
                        "_id": 0
                    }
                }
            ]
            results = list(dishes_collection.aggregate(pipeline))
            return [result["cook_method"] for result in results if result.get("cook_method")]
        except Exception as e:
            print(f"Error getting cook methods by ingredients: {e}")
            return []

    def get_all_ingredients(self) -> List[str]:
        """
        Lấy tất cả các nguyên liệu từ collection 'ingredients'
        """
        try:
            ingredients_collection = self.db.ingredients
            ingredients = list(ingredients_collection.find({}, {"name": 1, "_id": 0}))
            return [ingredient["name"] for ingredient in ingredients]
        except Exception as e:
            print(f"Error getting all ingredients: {e}")
            return []

# Tạo instance global
mongo_service = MongoService() 