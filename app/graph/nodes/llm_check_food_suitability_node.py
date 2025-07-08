import os
from typing import Dict, Any
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

PROMPT_TEMPLATE = (
    "Bạn là chuyên gia dinh dưỡng. Dựa trên các thông tin sau:\n"
    "- Cảm xúc: {emotion}\n"
    "- BMI: {bmi} ({bmi_category})\n"
    "- Bệnh lý: {medical_conditions}\n"
    "- Danh sách món ăn: {foods}\n"
    "- Chế độ ăn: {diets}\n"
    "- Phương pháp nấu: {methods}\n"
    "Hãy trả lời 'yes' nếu các món ăn trên phù hợp với người này, 'no' nếu không phù hợp.\n"
    "Chỉ trả lời đúng một từ: yes hoặc no."
)

def check_food_suitability(neo4j_result: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Kiểm tra sự phù hợp của món ăn với cảm xúc, bệnh lý, BMI bằng LLM
    
    Args:
        neo4j_result: Kết quả từ Neo4j query
        user_context: Thông tin người dùng (emotion, bmi_category, medical_conditions)
        
    Returns:
        dict: {"status": "success", "response": "yes/no", "reasoning": "..."}
    """
    try:
        # Trích xuất thông tin từ neo4j_result
        foods = neo4j_result.get("foods", {})
        emotion = user_context.get("emotion", "")
        bmi_category = user_context.get("bmi_category", "")
        medical_conditions = user_context.get("medical_conditions", [])
        
        # Tạo danh sách món ăn
        food_list = []
        for condition, food_data in foods.items():
            if isinstance(food_data, dict) and "advanced" in food_data:
                advanced_foods = food_data.get("advanced", [])
                for food in advanced_foods:
                    dish_name = food.get("dish_name", "")
                    if dish_name:
                        food_list.append(dish_name)
            else:
                # Dữ liệu cũ
                for food in food_data:
                    dish_name = food.get("dish_name", food.get("name", ""))
                    if dish_name:
                        food_list.append(dish_name)
        
        # Tạo danh sách chế độ ăn và phương pháp nấu
        diet_list = []
        method_list = []
        
        for condition, food_data in foods.items():
            if isinstance(food_data, dict) and "advanced" in food_data:
                advanced_foods = food_data.get("advanced", [])
                for food in advanced_foods:
                    diet_name = food.get("diet_name", "")
                    cook_method = food.get("cook_method", "")
                    if diet_name:
                        diet_list.append(diet_name)
                    if cook_method:
                        method_list.append(cook_method)
        
        # Loại bỏ duplicates
        food_list = list(set(food_list))[:10]  # Giới hạn 10 món
        diet_list = list(set(diet_list))[:5]   # Giới hạn 5 chế độ ăn
        method_list = list(set(method_list))[:5]  # Giới hạn 5 phương pháp
        
        # Tạo prompt
        prompt = PROMPT_TEMPLATE.format(
            emotion=emotion,
            bmi=bmi_category,
            bmi_category=bmi_category,
            medical_conditions=", ".join(medical_conditions),
            foods=", ".join(food_list),
            diets=", ".join(diet_list),
            methods=", ".join(method_list),
        )
        
        # Gọi OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.1
        )
        
        llm_response = response["choices"][0]["message"]["content"].strip().lower()
        
        # Xác định kết quả
        if "yes" in llm_response:
            result = "yes"
        elif "no" in llm_response:
            result = "no"
        else:
            result = "no"  # Default to no if unclear
        
        return {
            "status": "success",
            "response": result,
            "reasoning": llm_response,
            "foods_checked": food_list,
            "diets_checked": diet_list,
            "methods_checked": method_list
        }
        
    except Exception as e:
        return {
            "status": "error",
            "response": "no",
            "reasoning": f"Lỗi kiểm tra: {str(e)}",
            "error": str(e)
        } 