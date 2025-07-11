from typing import Dict, Any, List
from app.utils.prompt_templates import get_rerank_foods_prompt
from app.services.llm.llm_service import LLMService

def rerank_foods(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node rerank các món ăn sử dụng LLM theo thứ tự phù hợp nhất
    """
    try:
        user_data = state.get("user_data", {})
        bmi_result = state.get("bmi_result", {})
        selected_emotion = state.get("selected_emotion")
        selected_cooking_methods = state.get("selected_cooking_methods", [])
        aggregated_result = state.get("aggregated_result", {})
        
        # Lấy danh sách món ăn đã được tổng hợp
        if not aggregated_result or aggregated_result.get("status") != "success":
            return {"rerank_result": {"status": "error", "message": "Không có dữ liệu món ăn để rerank"}}
        
        aggregated_foods = aggregated_result.get("aggregated_foods", [])
        if not aggregated_foods:
            return {"rerank_result": {"status": "error", "message": "Danh sách món ăn trống"}}
        
        print(f"DEBUG: Reranking {len(aggregated_foods)} foods")
        
        # Lấy thông tin người dùng
        user_name = user_data.get("name", "Unknown")
        user_age = user_data.get("age", "N/A")
        bmi_category = bmi_result.get("bmi_category", "") if bmi_result else ""
        medical_conditions = user_data.get("medicalConditions", [])
        
        # Lọc bệnh thực sự
        real_conditions = []
        if medical_conditions:
            for condition in medical_conditions:
                condition_lower = condition.lower().strip()
                if condition_lower not in ["không có", "không bệnh", "không có bệnh", "bình thường", "khỏe mạnh"]:
                    real_conditions.append(condition)
        
        # Chuẩn bị dữ liệu cho LLM
        foods_data = []
        for food in aggregated_foods:
            food_info = {
                "id": food.get("dish_id", ""),
                "name": food.get("dish_name", "Unknown"),
                "description": food.get("description", ""),
                "cook_method": food.get("cook_method", ""),
                "diet": food.get("diet_name", ""),
                "bmi_category": food.get("bmi_category", ""),
                "calories": food.get("calories", 0),
                "protein": food.get("protein", 0),
                "fat": food.get("fat", 0),
                "carbs": food.get("carbs", 0)
            }
            foods_data.append(food_info)
        
        # Tạo prompt cho LLM
        prompt_data = {
            "user_name": user_name,
            "user_age": user_age,
            "bmi_category": bmi_category,
            "medical_conditions": real_conditions,
            "selected_emotion": selected_emotion,
            "selected_cooking_methods": selected_cooking_methods,
            "foods": foods_data
        }
        
        prompt = get_rerank_foods_prompt(prompt_data)
        
        print(f"DEBUG: Sending rerank request to LLM for {len(foods_data)} foods")
        
        # Gọi LLM để rerank
        try:
            llm_response = LLMService.get_completion(prompt)
            print(f"DEBUG: LLM response received: {len(llm_response)} characters")
            
            # Parse kết quả từ LLM
            ranked_foods = parse_llm_rerank_response(llm_response, aggregated_foods)
            
            if ranked_foods:
                print(f"DEBUG: Successfully reranked {len(ranked_foods)} foods")
                
                result = {
                    "status": "success",
                    "message": f"Đã rerank {len(ranked_foods)} món ăn theo thứ tự phù hợp",
                    "ranked_foods": ranked_foods,
                    "total_count": len(ranked_foods),
                    "rerank_criteria": {
                        "bmi_category": bmi_category,
                        "medical_conditions": real_conditions,
                        "emotion": selected_emotion,
                        "cooking_methods": selected_cooking_methods
                    }
                }
            else:
                print("DEBUG: Failed to parse LLM response, using original order")
                # Nếu không parse được, sử dụng thứ tự gốc
                result = {
                    "status": "success",
                    "message": f"Sử dụng thứ tự gốc cho {len(aggregated_foods)} món ăn",
                    "ranked_foods": aggregated_foods,
                    "total_count": len(aggregated_foods),
                    "rerank_criteria": {
                        "bmi_category": bmi_category,
                        "medical_conditions": real_conditions,
                        "emotion": selected_emotion,
                        "cooking_methods": selected_cooking_methods
                    }
                }
                
        except Exception as e:
            print(f"DEBUG: LLM error: {e}")
            # Nếu LLM lỗi, sử dụng thứ tự gốc
            result = {
                "status": "success",
                "message": f"Sử dụng thứ tự gốc cho {len(aggregated_foods)} món ăn (LLM error)",
                "ranked_foods": aggregated_foods,
                "total_count": len(aggregated_foods),
                "rerank_criteria": {
                    "bmi_category": bmi_category,
                    "medical_conditions": real_conditions,
                    "emotion": selected_emotion,
                    "cooking_methods": selected_cooking_methods
                }
            }
        
        return {"rerank_result": result}
        
    except Exception as e:
        return {"rerank_result": {"status": "error", "message": f"Lỗi rerank: {str(e)}"}}

def parse_llm_rerank_response(llm_response: str, original_foods: List[Dict]) -> List[Dict]:
    """
    Parse kết quả rerank từ LLM
    """
    try:
        # Tạo mapping từ tên món ăn đến object gốc
        food_mapping = {}
        for food in original_foods:
            food_name = food.get("dish_name", "").lower().strip()
            food_mapping[food_name] = food
        
        # Tìm các tên món ăn trong response của LLM
        ranked_foods = []
        lines = llm_response.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Tìm số thứ tự và tên món ăn
            # Format có thể là: "1. Tên món ăn" hoặc "1) Tên món ăn" hoặc "1- Tên món ăn"
            import re
            
            # Pattern để tìm số thứ tự và tên món ăn
            patterns = [
                r'^\d+\.\s*(.+)',  # 1. Tên món
                r'^\d+\)\s*(.+)',  # 1) Tên món
                r'^\d+-\s*(.+)',   # 1- Tên món
                r'^\d+\s+(.+)',    # 1 Tên món
            ]
            
            food_name = None
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    food_name = match.group(1).strip()
                    break
            
            if food_name:
                # Tìm món ăn trong mapping
                food_name_lower = food_name.lower().strip()
                for original_name, original_food in food_mapping.items():
                    if food_name_lower in original_name or original_name in food_name_lower:
                        if original_food not in ranked_foods:  # Tránh trùng lặp
                            ranked_foods.append(original_food)
                            break
        
        # Nếu không parse được đủ, thêm các món còn lại
        if len(ranked_foods) < len(original_foods):
            for food in original_foods:
                if food not in ranked_foods:
                    ranked_foods.append(food)
        
        print(f"DEBUG: Parsed {len(ranked_foods)} foods from LLM response")
        return ranked_foods
        
    except Exception as e:
        print(f"DEBUG: Error parsing LLM response: {e}")
        return [] 