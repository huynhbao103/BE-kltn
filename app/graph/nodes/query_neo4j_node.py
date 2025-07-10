from app.services.graph_schema_service import GraphSchemaService
from typing import Dict, Any, List

def query_neo4j_for_foods(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Truy vấn Neo4j nâng cao để tìm thực phẩm phù hợp
    """
    try:
        user_data = state.get("user_data", {})
        selected_emotion = state.get("selected_emotion")
        selected_cooking_methods = state.get("selected_cooking_methods", [])
        bmi_result = state.get("bmi_result", {})
        
        # Lấy danh sách tình trạng bệnh từ user_data
        medical_conditions = user_data.get("medicalConditions", [])
        
        # Lấy thông tin BMI
        bmi_category = bmi_result.get("bmi_category", "") if bmi_result else ""
        
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
        has_bmi = bmi_category and bmi_category.strip()
        
        # Debug prints
        print(f"DEBUG: has_conditions = {has_conditions}, real_conditions = {real_conditions}")
        print(f"DEBUG: has_emotion = {has_emotion}, selected_emotion = '{selected_emotion}'")
        print(f"DEBUG: has_cooking_methods = {has_cooking_methods}, selected_cooking_methods = {selected_cooking_methods}")
        print(f"DEBUG: has_bmi = {has_bmi}, bmi_category = '{bmi_category}'")
        
        # Nếu không có tiêu chí nào, trả về món ăn phổ biến
        if not has_conditions and not has_emotion and not has_cooking_methods and not has_bmi:
            print("DEBUG: No criteria found, returning popular foods")
            return query_popular_foods()

        all_foods = {}
        conditions_checked = []
        emotions_checked = []
        cooking_methods_checked = []
        bmi_checked = []
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
                print(f"DEBUG: Querying foods for emotion: {selected_emotion}")
                emotion_foods = GraphSchemaService.get_foods_by_emotion(selected_emotion)
                print(f"DEBUG: Found {len(emotion_foods) if emotion_foods else 0} foods for emotion")
                if emotion_foods:
                    all_foods[f"emotion_{selected_emotion}"] = {"advanced": emotion_foods, "source": "emotion"}
                    emotions_checked.append(selected_emotion)
            except Exception as e:
                print(f"Lỗi truy vấn cho emotion '{selected_emotion}': {str(e)}")

        # 3. Truy vấn dựa trên phương pháp nấu
        if has_cooking_methods:
            for method in selected_cooking_methods:
                try:
                    print(f"DEBUG: Querying foods for cooking method: {method}")
                    method_foods = GraphSchemaService.get_foods_by_cooking_method(method)
                    print(f"DEBUG: Found {len(method_foods) if method_foods else 0} foods for method {method}")
                    if method_foods:
                        all_foods[f"cooking_{method}"] = {"advanced": method_foods, "source": "cooking_method"}
                        cooking_methods_checked.append(method)
                except Exception as e:
                    print(f"Lỗi truy vấn cho cooking method '{method}': {str(e)}")

        # 4. Truy vấn dựa trên BMI
        if has_bmi:
            try:
                print(f"DEBUG: Querying foods for BMI category: {bmi_category}")
                bmi_foods = GraphSchemaService.get_foods_by_bmi(bmi_category.lower())
                print(f"DEBUG: Found {len(bmi_foods) if bmi_foods else 0} foods for BMI")
                if bmi_foods:
                    all_foods[f"bmi_{bmi_category}"] = {"advanced": bmi_foods, "source": "bmi"}
                    bmi_checked.append(bmi_category)
            except Exception as e:
                print(f"Lỗi truy vấn cho BMI '{bmi_category}': {str(e)}")

        print(f"DEBUG: all_foods keys = {list(all_foods.keys())}")
        print(f"DEBUG: all_foods count = {len(all_foods)}")
        
        if not all_foods:
            print("DEBUG: No foods found, returning all foods as fallback")
            # Fallback: trả về tất cả món ăn nếu không tìm thấy theo tiêu chí
            all_foods_result = query_all_foods()
            return all_foods_result

        result = {
            "status": "success",
            "message": "Tìm thấy món ăn phù hợp.",
            "foods": all_foods,
            "conditions_checked": conditions_checked,
            "emotions_checked": emotions_checked,
            "cooking_methods_checked": cooking_methods_checked,
            "bmi_checked": bmi_checked,
            "diet_recommendations": all_diet_recommendations,
            "cook_methods": all_cook_methods,
        }
        
        print(f"DEBUG: Returning result with {len(all_foods)} food categories")
        # Trả về chỉ phần thay đổi của state theo quy tắc LangGraph
        return {"query_result": result}
    except Exception as e:
        return {"query_result": {"status": "error", "message": str(e)}}

def query_popular_foods(message="Đây là những món ăn phổ biến."):
    """Truy vấn thực phẩm phổ biến."""
    try:
        popular_foods = GraphSchemaService.get_popular_foods()
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

