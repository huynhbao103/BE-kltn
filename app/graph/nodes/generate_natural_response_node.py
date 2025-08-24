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
        aggregated_result = state.get("aggregated_result", {})
        neo4j_result = state.get("neo4j_result", {})
        filtered_result = state.get("filtered_result", {})
        
        # Kiểm tra nếu rerank LLM đã cung cấp lời giải thích
        if (rerank_result and 
            rerank_result.get("status") == "llm_explanation_provided" and 
            rerank_result.get("llm_explanation")):
            # Lấy lời giải thích từ rerank LLM
            llm_explanation = rerank_result.get("llm_explanation")
            
            # Kết hợp với gợi ý thay thế
            combined_response = f"""Tôi rất tiếc nhưng danh sách món ăn hiện tại có món chứa nguyên liệu mà bạn bị dị ứng.

{llm_explanation}

Để thay đổi, bạn có thể xem xét thêm các món ăn chế biến từ rau cải, hạt, hoặc đậu phụ để đảm bảo cung cấp đủ chất dinh dưỡng. Đồng thời, hãy thêm vào chế độ ăn uống hàng ngày của bạn các loại thực phẩm giàu chất xơ và protein thực vật để duy trì sức khỏe tốt. Chúc bạn có bữa ăn ngon miệng và bổ dưỡng!"""
            
            print(f"[DEBUG] Using LLM explanation from rerank and adding suggestions")
            return {
                **state,
                "natural_response": combined_response.strip(),
                "step": "natural_response_from_llm_explanation"
            }
        
        # Lấy danh sách món ăn đã rerank
        ranked_foods = rerank_result.get("ranked_foods", []) if rerank_result else []
        
        # Kiểm tra dị ứng từ nguyên liệu và tạo cảnh báo
        allergy_warnings = []
        if filtered_result and filtered_result.get("allergy_warnings"):
            allergy_warnings = filtered_result.get("allergy_warnings", {})
            print(f"[DEBUG] Found allergy warnings: {allergy_warnings}")
        
        # Tạo thông tin cảnh báo dị ứng
        allergy_alert = ""
        if allergy_warnings:
            allergy_alert = "\n⚠️ CẢNH BÁO DỊ ỨNG:\n"
            for source_key, warnings in allergy_warnings.items():
                for warning in warnings:
                    dish_name = warning.get("dish_name", "Unknown")
                    warning_text = warning.get("warnings", [])
                    if warning_text:
                        allergy_alert += f"• {dish_name}: {', '.join(warning_text)}\n"
            print(f"[DEBUG] Generated allergy alert: {allergy_alert}")
        
        # Debug: Kiểm tra thông tin user allergies
        user_allergies = user_data.get("allergies", [])
        print(f"[DEBUG] User allergies: {user_allergies}")
        print(f"[DEBUG] Has allergy warnings: {bool(allergy_warnings)}")
        
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
        
        # Thu thập thông tin constraints để giải thích cho LLM
        constraints_info = {
            "bmi_checked": neo4j_result.get("bmi_checked", []),
            "conditions_checked": neo4j_result.get("conditions_checked", []),
            "cooking_methods_checked": neo4j_result.get("cooking_methods_checked", []),
            "aggregated_status": aggregated_result.get("status", ""),
            "aggregated_message": aggregated_result.get("message", ""),
            "has_foods": len(ranked_foods) > 0,
            "excluded_methods": state.get("excluded_cooking_methods", []),
            "allergy_warnings": allergy_warnings,  # Thêm thông tin cảnh báo dị ứng
            "allergy_alert": allergy_alert  # Thêm cảnh báo dị ứng
        }
        
        # Tạo prompt cho LLM
        prompt = get_natural_response_prompt(
            question=question,
            user_info=user_info,
            food_info=food_info,
            cooking_methods=selected_cooking_methods,
            weather=weather,
            time_of_day=time_of_day,
            topic_classification=topic_classification,
            constraints_info=constraints_info
        )
        
        # Gọi LLM để tạo câu trả lời tự nhiên
        natural_response = LLMService.get_completion(prompt)
        
        # Thêm cảnh báo dị ứng vào câu trả lời nếu có
        if allergy_alert:
            natural_response = allergy_alert + "\n" + natural_response
        
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