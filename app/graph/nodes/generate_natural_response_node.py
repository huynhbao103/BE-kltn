from typing import Dict, Any, List
from app.services.llm.llm_service import LLMService
from app.utils.prompt_templates import get_natural_response_prompt

def generate_natural_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node tạo câu trả lời tự nhiên bằng LLM sau khi đã có kết quả rerank
    """
    try:
        # Lấy thông tin từ state
        user_data = state.get("user_data", {})
        question = state.get("question", "")
        topic_classification = state.get("topic_classification", "")
        bmi_result = state.get("bmi_result", {})
        rerank_result = state.get("rerank_result", {})
        selected_cooking_methods = state.get("selected_cooking_methods", [])
        weather = state.get("weather", "")
        time_of_day = state.get("time_of_day", "")
        
        # Lấy danh sách món ăn đã rerank
        ranked_foods = rerank_result.get("ranked_foods", []) if rerank_result else []
        
        if not ranked_foods:
            return {
                **state,
                "natural_response": "Xin lỗi, tôi không tìm thấy món ăn nào phù hợp với yêu cầu của bạn.",
                "step": "natural_response_generated"
            }
        
        # Chuẩn bị thông tin cho LLM
        user_info = {
            "name": user_data.get("name", "Unknown"),
            "age": user_data.get("age", "N/A"),
            "bmi": bmi_result.get("bmi", "N/A") if bmi_result else "N/A",
            "bmi_category": bmi_result.get("bmi_category", "N/A") if bmi_result else "N/A",
            "medical_conditions": user_data.get("medicalConditions", []),
            "allergies": user_data.get("allergies", [])
        }
        
        # Lấy thông tin món ăn
        food_info = []
        for food in ranked_foods[:10]:  # Giới hạn 10 món đầu để tránh prompt quá dài
            food_info.append({
                "name": food.get("dish_name", "Unknown"),
                "description": food.get("description", ""),
                "cook_method": food.get("cook_method", ""),
                "diet": food.get("diet_name", ""),
                "calories": food.get("calories", 0),
                "protein": food.get("protein", 0),
                "fat": food.get("fat", 0),
                "carbs": food.get("carbs", 0)
            })
        
        # Tạo prompt cho LLM
        prompt = get_natural_response_prompt(
            question=question,
            user_info=user_info,
            food_info=food_info,
            cooking_methods=selected_cooking_methods,
            weather=weather,
            time_of_day=time_of_day,
            topic_classification=topic_classification
        )
        
        # Gọi LLM để tạo câu trả lời tự nhiên
        natural_response = LLMService.get_completion(prompt)
        
        return {
            **state,
            "natural_response": natural_response,
            "step": "natural_response_generated"
        }
        
    except Exception as e:
        return {
            **state,
            "error": f"Lỗi tạo câu trả lời tự nhiên: {str(e)}",
            "step": "natural_response_error"
        } 