from app.services.neo4j_service import neo4j_service
from app.services.graph_schema_service import GraphSchemaService
from typing import Dict, Any, List

def query_neo4j_for_foods(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Truy vấn Neo4j nâng cao để tìm thực phẩm phù hợp dựa trên tình trạng bệnh của người dùng
    Sử dụng schema graph để tạo các truy vấn chi tiết hơn
    
    Args:
        user_data: Thông tin người dùng từ MongoDB
        
    Returns:
        Dict chứa kết quả truy vấn Neo4j với thông tin chi tiết
    """
    try:
        # Lấy danh sách tình trạng bệnh từ user_data
        medical_conditions = user_data.get("medicalConditions", [])
        
        if not medical_conditions or medical_conditions == ["Không có"]:
            return {
                "status": "no_conditions",
                "message": "Người dùng không có tình trạng bệnh đặc biệt",
                "foods": [],
                "conditions_checked": [],
                "diet_recommendations": [],
                "cook_methods": [],
                "detailed_analysis": {}
            }
        
        # Kết quả tổng hợp
        all_foods = {}
        conditions_checked = []
        all_diet_recommendations = {}
        all_cook_methods = {}
        detailed_analysis = {}
        
        for condition in medical_conditions:
            try:
                # 1. Truy vấn thực phẩm cơ bản
                basic_foods = neo4j_service.get_foods_by_condition(condition)
                
                # 2. Truy vấn thực phẩm nâng cao với thông tin chi tiết
                advanced_foods = GraphSchemaService.get_foods_by_disease_advanced(condition)
                
                # 3. Truy vấn chế độ ăn
                diet_recommendations = GraphSchemaService.get_diet_recommendations_by_disease(condition)
                
                # 4. Truy vấn phương pháp nấu
                cook_methods = GraphSchemaService.get_cook_methods_by_disease(condition)
                
                # Tổng hợp kết quả cho condition này
                condition_result = {
                    "basic_foods": basic_foods,
                    "advanced_foods": advanced_foods,
                    "diet_recommendations": diet_recommendations,
                    "cook_methods": cook_methods,
                    "food_count": len(advanced_foods) if advanced_foods else 0,
                    "diet_count": len(diet_recommendations),
                    "cook_method_count": len(cook_methods)
                }
                
                # Lưu vào kết quả tổng hợp
                if basic_foods or advanced_foods:
                    all_foods[condition] = {
                        "basic": basic_foods,
                        "advanced": advanced_foods
                    }
                    conditions_checked.append(condition)
                
                if diet_recommendations:
                    all_diet_recommendations[condition] = diet_recommendations
                
                if cook_methods:
                    all_cook_methods[condition] = cook_methods
                
                detailed_analysis[condition] = condition_result
                
            except Exception as e:
                print(f"Lỗi truy vấn cho condition '{condition}': {str(e)}")
                continue
        
        # Tạo kết quả chi tiết
        if all_foods:
            # Tính toán thống kê
            # Đếm số lượng món ăn duy nhất (theo id hoặc tên)
            unique_dish_ids = set()
            for foods in all_foods.values():
                if isinstance(foods, dict) and "advanced" in foods:
                    for food in foods["advanced"]:
                        key = food.get("dish_id") or food.get("id") or food.get("dish_name") or food.get("name")
                        unique_dish_ids.add(key)
                else:
                    for food in foods:
                        key = food.get("dish_id") or food.get("id") or food.get("dish_name") or food.get("name")
                        unique_dish_ids.add(key)
            total_foods = len(unique_dish_ids)
            total_diets = len(set([diet for diets in all_diet_recommendations.values() for diet in diets]))
            total_cook_methods = len(set([method for methods in all_cook_methods.values() for method in methods]))
            
            return {
                "status": "success",
                "message": f"Tìm thấy {total_foods} món ăn phù hợp cho {len(conditions_checked)} tình trạng bệnh",
                "foods": all_foods,
                "conditions_checked": conditions_checked,
                "diet_recommendations": all_diet_recommendations,
                "cook_methods": all_cook_methods,
                "detailed_analysis": detailed_analysis,
                "statistics": {
                    "total_conditions": len(conditions_checked),
                    "total_foods": total_foods,
                    "total_diets": total_diets,
                    "total_cook_methods": total_cook_methods,
                    "average_foods_per_condition": total_foods / len(conditions_checked) if conditions_checked else 0
                }
            }
        else:
            return {
                "status": "no_foods_found",
                "message": "Không tìm thấy thực phẩm phù hợp cho các tình trạng bệnh",
                "foods": {},
                "conditions_checked": [],
                "diet_recommendations": {},
                "cook_methods": {},
                "detailed_analysis": {},
                "statistics": {
                    "total_conditions": 0,
                    "total_foods": 0,
                    "total_diets": 0,
                    "total_cook_methods": 0,
                    "average_foods_per_condition": 0
                }
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Lỗi truy vấn Neo4j: {str(e)}",
            "foods": {},
            "conditions_checked": [],
            "diet_recommendations": {},
            "cook_methods": {},
            "detailed_analysis": {},
            "statistics": {
                "total_conditions": 0,
                "total_foods": 0,
                "total_diets": 0,
                "total_cook_methods": 0,
                "average_foods_per_condition": 0
            }
        } 