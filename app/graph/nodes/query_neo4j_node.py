from app.services.neo4j_service import neo4j_service
from app.services.graph_schema_service import GraphSchemaService
from typing import Dict, Any, List

def query_neo4j_for_foods(user_data: Dict[str, Any], selected_emotion: str = None, selected_cooking_methods: List[str] = None) -> Dict[str, Any]:
    """
    Truy vấn Neo4j nâng cao để tìm thực phẩm phù hợp
    """
    try:
        # Lấy danh sách tình trạng bệnh từ user_data
        medical_conditions = user_data.get("medicalConditions", [])
        
        # Kiểm tra có bệnh thực sự hay không
        real_conditions = []
        if medical_conditions:
            for condition in medical_conditions:
                condition_lower = condition.lower().strip()
                if condition_lower not in ["không có", "không bệnh", "không có bệnh", "bình thường", "khỏe mạnh"]:
                    real_conditions.append(condition)
        
        has_conditions = len(real_conditions) > 0
        has_emotion = selected_emotion and selected_emotion.strip()
        has_cooking_methods = selected_cooking_methods and len(selected_cooking_methods) > 0
        
        # Nếu không có tiêu chí nào, trả về món ăn phổ biến
        if not has_conditions and not has_emotion and not has_cooking_methods:
            return query_popular_foods()

        all_foods = {}
        conditions_checked = []
        emotions_checked = []
        cooking_methods_checked = []
        all_diet_recommendations = {}
        all_cook_methods = {}
        detailed_analysis = {}

        # 1. Truy vấn dựa trên bệnh
        if has_conditions:
            for condition in real_conditions:
                try:
                    advanced_foods = GraphSchemaService.get_foods_by_disease_advanced(condition)
                    if advanced_foods:
                        all_foods[f"condition_{condition}"] = {"advanced": advanced_foods, "source": "medical_condition"}
                        conditions_checked.append(condition)
                        all_diet_recommendations[condition] = GraphSchemaService.get_diet_recommendations_by_disease(condition)
                        all_cook_methods[condition] = GraphSchemaService.get_cook_methods_by_disease(condition)
                except Exception as e:
                    print(f"Lỗi truy vấn cho condition '{condition}': {str(e)}")

        # 2. Truy vấn dựa trên cảm xúc
        if has_emotion:
            try:
                emotion_foods = GraphSchemaService.get_foods_by_emotion(selected_emotion)
                if emotion_foods:
                    all_foods[f"emotion_{selected_emotion}"] = {"advanced": emotion_foods, "source": "emotion"}
                    emotions_checked.append(selected_emotion)
            except Exception as e:
                print(f"Lỗi truy vấn cho emotion '{selected_emotion}': {str(e)}")

        # 3. Truy vấn dựa trên phương pháp nấu
        if has_cooking_methods:
            for method in selected_cooking_methods:
                try:
                    method_foods = GraphSchemaService.get_foods_by_cooking_method(method)
                    if method_foods:
                        all_foods[f"cooking_{method}"] = {"advanced": method_foods, "source": "cooking_method"}
                        cooking_methods_checked.append(method)
                except Exception as e:
                    print(f"Lỗi truy vấn cho cooking method '{method}': {str(e)}")

        if not all_foods:
            return query_popular_foods("Không tìm thấy món ăn phù hợp, đây là các món phổ biến.")

        return {
            "status": "success",
            "message": "Tìm thấy món ăn phù hợp.",
            "foods": all_foods,
            "conditions_checked": conditions_checked,
            "emotions_checked": emotions_checked,
            "cooking_methods_checked": cooking_methods_checked,
            "diet_recommendations": all_diet_recommendations,
            "cook_methods": all_cook_methods,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def query_popular_foods(message="Đây là những món ăn phổ biến."):
    """Truy vấn thực phẩm phổ biến."""
    try:
        popular_foods = GraphSchemaService.get_popular_foods()
        return {
            "status": "popular_foods",
            "message": message,
            "foods": {"popular": {"advanced": popular_foods, "source": "popular"}},
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def query_all_foods() -> Dict[str, Any]:
    """
    Truy vấn tất cả món ăn khi không có bệnh hoặc thông tin cụ thể
    """
    try:
        # Truy vấn tất cả món ăn từ Neo4j cho người khỏe mạnh
        all_foods = neo4j_service.get_all_foods_for_healthy_person()
        
        return {
            "status": "all_foods",
            "message": "Đây là tất cả các món ăn có sẵn (không có bệnh cần lọc)",
            "foods": {
                "all_foods": {
                    "basic": [],
                    "advanced": all_foods,
                    "source": "all_foods",
                    "description": "Tất cả món ăn có sẵn"
                }
            },
            "conditions_checked": [],
            "emotions_checked": [],
            "cooking_methods_checked": [],
            "diet_recommendations": {},
            "cook_methods": {},
            "detailed_analysis": {
                "all_foods": {
                    "all_foods": all_foods,
                    "food_count": len(all_foods),
                    "source": "all_foods"
                }
            },
            "statistics": {
                "total_conditions": 0,
                "total_emotions": 0,
                "total_cooking_methods": 0,
                "total_foods": len(all_foods),
                "total_diets": 0,
                "total_cook_methods": 0,
                "average_foods_per_source": len(all_foods)
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Lỗi truy vấn tất cả món ăn: {str(e)}",
            "foods": {},
            "conditions_checked": [],
            "emotions_checked": [],
            "cooking_methods_checked": [],
            "diet_recommendations": {},
            "cook_methods": {},
            "detailed_analysis": {},
            "statistics": {
                "total_conditions": 0,
                "total_emotions": 0,
                "total_cooking_methods": 0,
                "total_foods": 0,
                "total_diets": 0,
                "total_cook_methods": 0,
                "average_foods_per_source": 0
            }
        }

def query_popular_foods() -> Dict[str, Any]:
    """
    Truy vấn thực phẩm phổ biến khi không có thông tin cụ thể
    """
    try:
        # Truy vấn thực phẩm phổ biến từ Neo4j (không giới hạn cho test)
        popular_foods = neo4j_service.get_popular_foods()
        
        return {
            "status": "popular_foods",
            "message": "Đây là những món ăn phổ biến và tốt cho sức khỏe",
            "foods": {
                "popular": {
                    "basic": [],
                    "advanced": popular_foods,
                    "source": "popular",
                    "description": "Thực phẩm phổ biến và tốt cho sức khỏe"
                }
            },
            "conditions_checked": [],
            "emotions_checked": [],
            "cooking_methods_checked": [],
            "diet_recommendations": {},
            "cook_methods": {},
            "detailed_analysis": {
                "popular": {
                    "popular_foods": popular_foods,
                    "food_count": len(popular_foods),
                    "source": "popular"
                }
            },
            "statistics": {
                "total_conditions": 0,
                "total_emotions": 0,
                "total_cooking_methods": 0,
                "total_foods": len(popular_foods),
                "total_diets": 0,
                "total_cook_methods": 0,
                "average_foods_per_source": len(popular_foods)
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Lỗi truy vấn thực phẩm phổ biến: {str(e)}",
            "foods": {},
            "conditions_checked": [],
            "emotions_checked": [],
            "cooking_methods_checked": [],
            "diet_recommendations": {},
            "cook_methods": {},
            "detailed_analysis": {},
            "statistics": {
                "total_conditions": 0,
                "total_emotions": 0,
                "total_cooking_methods": 0,
                "total_foods": 0,
                "total_diets": 0,
                "total_cook_methods": 0,
                "average_foods_per_source": 0
            }
        } 