from typing import Dict, Any, List

def rerank_foods_by_suitability(foods_data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sắp xếp lại danh sách món ăn theo mức độ phù hợp với người dùng
    
    Args:
        foods_data: Dữ liệu thực phẩm từ Neo4j
        user_context: Thông tin người dùng (cảm xúc, BMI, bệnh lý)
        
    Returns:
        Dict chứa danh sách món ăn đã được sắp xếp lại
    """
    try:
        emotion = user_context.get("emotion", "")
        bmi_category = user_context.get("bmi_category", "")
        medical_conditions = user_context.get("medical_conditions", [])
        
        # Tạo danh sách món ăn đã sắp xếp
        reranked_foods = {}
        
        for condition, food_data in foods_data.get("foods", {}).items():
            if isinstance(food_data, dict) and "advanced" in food_data:
                advanced_foods = food_data.get("advanced", [])
                
                # Sắp xếp theo tiêu chí phù hợp
                scored_foods = []
                for food in advanced_foods:
                    score = 0
                    dish_name = food.get("dish_name", "").lower()
                    cook_method = food.get("cook_method", "").lower()
                    diet_name = food.get("diet_name", "").lower()
                    
                    # Điểm cho cảm xúc
                    if emotion == "Mệt mỏi":
                        if "súp" in dish_name or "súp" in cook_method:
                            score += 3
                        if "hấp" in cook_method:
                            score += 2
                    elif emotion == "Tức giận":
                        if "gỏi" in dish_name or "salad" in dish_name:
                            score += 3
                        if "luộc" in cook_method:
                            score += 2
                    elif emotion == "Vui vẻ":
                        if "nướng" in cook_method or "xiên" in dish_name:
                            score += 3
                    
                    # Điểm cho BMI
                    if bmi_category == "Gầy":
                        if "thịt" in dish_name or "gà" in dish_name or "cá" in dish_name:
                            score += 2
                    elif "Béo phì" in bmi_category:
                        if "rau" in dish_name or "gỏi" in dish_name:
                            score += 2
                    
                    # Điểm cho bệnh lý
                    if "Đái tháo đường" in condition:
                        if "gạo lứt" in dish_name or "khoai lang" in dish_name:
                            score += 3
                        if "ít đường" in diet_name or "kiểm soát đường" in diet_name:
                            score += 2
                    
                    scored_foods.append((food, score))
                
                # Sắp xếp theo điểm số giảm dần
                scored_foods.sort(key=lambda x: x[1], reverse=True)
                reranked_foods[condition] = {
                    "basic": food_data.get("basic", []),
                    "advanced": [food for food, score in scored_foods],
                    "scores": {food.get("dish_name", ""): score for food, score in scored_foods}
                }
            else:
                # Dữ liệu cũ, giữ nguyên
                reranked_foods[condition] = food_data
        
        return {
            "status": "success",
            "message": "Đã sắp xếp lại danh sách món ăn theo mức độ phù hợp",
            "foods": reranked_foods,
            "conditions_checked": foods_data.get("conditions_checked", []),
            "diet_recommendations": foods_data.get("diet_recommendations", {}),
            "cook_methods": foods_data.get("cook_methods", {}),
            "detailed_analysis": foods_data.get("detailed_analysis", {}),
            "statistics": foods_data.get("statistics", {}),
            "reranked": True
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Lỗi sắp xếp lại món ăn: {str(e)}",
            "foods": foods_data.get("foods", {}),
            "reranked": False
        } 