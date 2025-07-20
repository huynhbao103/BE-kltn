from app.services.graph_schema_service import GraphSchemaService
from typing import Dict, Any, List

def query_neo4j_for_foods(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Truy vấn Neo4j nâng cao để tìm thực phẩm phù hợp
    """
    try:
        user_data = state.get("user_data", {})
        selected_cooking_methods = state.get("selected_cooking_methods", [])
        bmi_result = state.get("bmi_result", {})
        medical_conditions = user_data.get("medicalConditions", [])
        previous_food_ids = state.get("previous_food_ids", [])  # Lấy danh sách ID đã gợi ý
        
        bmi_category = bmi_result.get("bmi_category", "") if bmi_result else ""
        real_conditions = []
        if medical_conditions:
            for condition in medical_conditions:
                condition_lower = condition.lower().strip()
                if condition_lower not in ["không có", "không bệnh", "không có bệnh", "bình thường", "khỏe mạnh"]:
                    real_conditions.append(condition)
        has_conditions = len(real_conditions) > 0
        has_cooking_methods = selected_cooking_methods and len(selected_cooking_methods) > 0
        has_bmi = bmi_category and bmi_category.strip()

        all_foods = {}
        conditions_checked = []
        cooking_methods_checked = []
        bmi_checked = []
        all_diet_recommendations = {}
        all_cook_methods = {}
        detailed_analysis = {}

        # 1. Lọc theo bệnh
        if has_conditions:
            for condition in real_conditions:
                advanced_foods = GraphSchemaService.get_foods_by_disease_advanced(condition, excluded_ids=previous_food_ids)
                if advanced_foods:
                    all_foods[f"condition_{condition}"] = {"advanced": advanced_foods, "source": "medical_condition"}
                    conditions_checked.append(condition)
                    all_diet_recommendations[condition] = GraphSchemaService.get_diet_recommendations_by_disease(condition)
                    all_cook_methods[condition] = GraphSchemaService.get_cook_methods_by_disease(condition)
        # 2. Lọc theo BMI
        if has_bmi:
            bmi_foods = GraphSchemaService.get_foods_by_bmi(bmi_category.lower(), excluded_ids=previous_food_ids)
            if bmi_foods:
                all_foods[f"bmi_{bmi_category}"] = {"advanced": bmi_foods, "source": "bmi"}
                bmi_checked.append(bmi_category)
        # 3. Lọc theo phương pháp nấu
        if has_cooking_methods:
            for method in selected_cooking_methods:
                method_foods = GraphSchemaService.get_foods_by_cooking_method(method, excluded_ids=previous_food_ids)
                if method_foods:
                    all_foods[f"cooking_{method}"] = {"advanced": method_foods, "source": "cooking_method"}
                    cooking_methods_checked.append(method)
        # Nếu không có tiêu chí nào, trả về món ăn phổ biến
        if not all_foods:
            return query_popular_foods(excluded_ids=previous_food_ids)
        # 5. Lọc theo context (weather + time_of_day)
        weather = state.get("weather")
        time_of_day = state.get("time_of_day")
        context_name = None
        suggested_cook_methods = []
        if weather and time_of_day:
            context_name, suggested_cook_methods = GraphSchemaService.get_context_and_cook_methods(weather, time_of_day)
            if suggested_cook_methods:
                filtered_all_foods = {}
                for key, value in all_foods.items():
                    advanced_foods = value.get("advanced", [])
                    filtered_advanced = [food for food in advanced_foods if food.get("cook_method") in suggested_cook_methods]
                    if filtered_advanced:
                        filtered_all_foods[key] = {**value, "advanced": filtered_advanced}
                if filtered_all_foods:
                    all_foods = filtered_all_foods
                else:
                    # Giữ nguyên kết quả nếu lọc context không còn món nào
                    pass
        result = {
            "status": "success",
            "message": "Tìm thấy món ăn phù hợp.",
            "foods": all_foods,
            "conditions_checked": conditions_checked,
            "cooking_methods_checked": cooking_methods_checked,
            "bmi_checked": bmi_checked,
            "diet_recommendations": all_diet_recommendations,
            "cook_methods": all_cook_methods,
        }
        return {"query_result": result}
    except Exception as e:
        return {"query_result": {"status": "error", "message": str(e)}}

def query_popular_foods(message="Đây là những món ăn phổ biến.", excluded_ids: List[str] = None):
    """Truy vấn thực phẩm phổ biến."""
    try:
        popular_foods = GraphSchemaService.get_popular_foods(excluded_ids=excluded_ids)
        result = {
            "status": "popular_foods",
            "message": message,
            "foods": {"popular": {"advanced": popular_foods, "source": "popular"}},
        }
        # Trả về đúng format cho LangGraph
        return {"query_result": result}
    except Exception as e:
        return {"query_result": {"status": "error", "message": str(e)}}

def query_all_foods() -> Dict[str, Any]:
    """
    Truy vấn tất cả món ăn khi không có bệnh hoặc thông tin cụ thể
    """
    try:
        # Truy vấn tất cả món ăn từ GraphSchemaService cho người khỏe mạnh
        all_foods = GraphSchemaService.get_all_foods_for_healthy_person()
        
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
                "total_cooking_methods": 0,
                "total_foods": 0,
                "total_diets": 0,
                "total_cook_methods": 0,
                "average_foods_per_source": 0
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Lỗi truy vấn tất cả món ăn: {str(e)}",
            "foods": {},
            "conditions_checked": [],
            "cooking_methods_checked": [],
            "diet_recommendations": {},
            "cook_methods": {},
            "detailed_analysis": {},
            "statistics": {
                "total_conditions": 0,
                "total_cooking_methods": 0,
                "total_foods": 0,
                "total_diets": 0,
                "total_cook_methods": 0,
                "average_foods_per_source": 0
            }
        }

