from app.services.neo4j_service import neo4j_service
from app.services.graph_schema_service import GraphSchemaService
from typing import Dict, Any, List

def query_neo4j_for_foods(user_data: Dict[str, Any], selected_emotion: str = None, selected_cooking_methods: List[str] = None) -> Dict[str, Any]:
    """
    Truy vấn Neo4j nâng cao để tìm thực phẩm phù hợp
    Có thể truy vấn dựa trên:
    1. Tình trạng bệnh của người dùng
    2. Cảm xúc hiện tại
    3. Phương pháp nấu ưa thích
    4. Hoặc kết hợp tất cả
    
    Args:
        user_data: Thông tin người dùng từ MongoDB
        selected_emotion: Cảm xúc đã chọn (optional)
        selected_cooking_methods: Phương pháp nấu đã chọn (optional)
        
    Returns:
        Dict chứa kết quả truy vấn Neo4j với thông tin chi tiết
    """
    try:
        # Lấy danh sách tình trạng bệnh từ user_data
        medical_conditions = user_data.get("medicalConditions", [])
        
        # Kiểm tra xem có thông tin gì để truy vấn không
        has_conditions = medical_conditions and medical_conditions != ["Không có"]
        has_emotion = selected_emotion and selected_emotion.strip()
        has_cooking_methods = selected_cooking_methods and len(selected_cooking_methods) > 0
        
        # Nếu không có thông tin gì, trả về thực phẩm phổ biến
        if not has_conditions and not has_emotion and not has_cooking_methods:
            return query_popular_foods()
        
        # Kết quả tổng hợp
        all_foods = {}
        conditions_checked = []
        emotions_checked = []
        cooking_methods_checked = []
        all_diet_recommendations = {}
        all_cook_methods = {}
        detailed_analysis = {}
        
        # 1. Truy vấn dựa trên tình trạng bệnh
        if has_conditions:
            for condition in medical_conditions:
                try:
                    # Truy vấn thực phẩm cơ bản
                    basic_foods = neo4j_service.get_foods_by_condition(condition)
                    
                    # Truy vấn thực phẩm nâng cao với thông tin chi tiết
                    advanced_foods = GraphSchemaService.get_foods_by_disease_advanced(condition)
                    
                    # Truy vấn chế độ ăn
                    diet_recommendations = GraphSchemaService.get_diet_recommendations_by_disease(condition)
                    
                    # Truy vấn phương pháp nấu
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
                        all_foods[f"condition_{condition}"] = {
                            "basic": basic_foods,
                            "advanced": advanced_foods,
                            "source": "medical_condition",
                            "condition": condition
                        }
                        conditions_checked.append(condition)
                    
                    if diet_recommendations:
                        all_diet_recommendations[condition] = diet_recommendations
                    
                    if cook_methods:
                        all_cook_methods[condition] = cook_methods
                    
                    detailed_analysis[f"condition_{condition}"] = condition_result
                    
                except Exception as e:
                    print(f"Lỗi truy vấn cho condition '{condition}': {str(e)}")
                    continue
        
        # 2. Truy vấn dựa trên cảm xúc
        if has_emotion:
            try:
                emotion_foods = GraphSchemaService.get_foods_by_emotion(selected_emotion)
                if emotion_foods:
                    all_foods[f"emotion_{selected_emotion}"] = {
                        "basic": [],
                        "advanced": emotion_foods,
                        "source": "emotion",
                        "emotion": selected_emotion
                    }
                    emotions_checked.append(selected_emotion)
                    
                    detailed_analysis[f"emotion_{selected_emotion}"] = {
                        "emotion_foods": emotion_foods,
                        "food_count": len(emotion_foods),
                        "source": "emotion"
                    }
            except Exception as e:
                print(f"Lỗi truy vấn cho emotion '{selected_emotion}': {str(e)}")
        
        # 3. Truy vấn dựa trên phương pháp nấu
        if has_cooking_methods:
            for method in selected_cooking_methods:
                try:
                    method_foods = GraphSchemaService.get_foods_by_cooking_method(method)
                    if method_foods:
                        all_foods[f"cooking_{method}"] = {
                            "basic": [],
                            "advanced": method_foods,
                            "source": "cooking_method",
                            "method": method
                        }
                        cooking_methods_checked.append(method)
                        
                        detailed_analysis[f"cooking_{method}"] = {
                            "method_foods": method_foods,
                            "food_count": len(method_foods),
                            "source": "cooking_method"
                        }
                except Exception as e:
                    print(f"Lỗi truy vấn cho cooking method '{method}': {str(e)}")
                    continue
        
        # Tạo kết quả chi tiết
        if all_foods:
            # Tính toán thống kê
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
            
            # Tạo message mô tả
            sources = []
            if conditions_checked:
                sources.append(f"{len(conditions_checked)} tình trạng bệnh")
            if emotions_checked:
                sources.append(f"cảm xúc {', '.join(emotions_checked)}")
            if cooking_methods_checked:
                sources.append(f"phương pháp nấu {', '.join(cooking_methods_checked)}")
            
            message = f"Tìm thấy {total_foods} món ăn phù hợp dựa trên {' và '.join(sources)}"
            
            return {
                "status": "success",
                "message": message,
                "foods": all_foods,
                "conditions_checked": conditions_checked,
                "emotions_checked": emotions_checked,
                "cooking_methods_checked": cooking_methods_checked,
                "diet_recommendations": all_diet_recommendations,
                "cook_methods": all_cook_methods,
                "detailed_analysis": detailed_analysis,
                "statistics": {
                    "total_conditions": len(conditions_checked),
                    "total_emotions": len(emotions_checked),
                    "total_cooking_methods": len(cooking_methods_checked),
                    "total_foods": total_foods,
                    "total_diets": total_diets,
                    "total_cook_methods": total_cook_methods,
                    "average_foods_per_source": total_foods / len(all_foods) if all_foods else 0
                }
            }
        else:
            # Nếu không tìm thấy gì, trả về thực phẩm phổ biến
            return query_popular_foods()
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Lỗi truy vấn Neo4j: {str(e)}",
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