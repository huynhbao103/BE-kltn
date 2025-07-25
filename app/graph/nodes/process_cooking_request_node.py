from typing import Dict, Any, List
from app.graph.nodes.classify_topic_node import extract_cooking_methods
from app.services.graph_schema_service import GraphSchemaService

def process_cooking_request(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Xử lý yêu cầu cooking method từ user.
    Trích xuất cooking methods từ câu hỏi và kiểm tra tính phù hợp với bệnh.
    Nếu nhận được ['ALL'] thì trả về tất cả các món.
    """
    try:
        question = state.get("question", "")
        user_data = state.get("user_data", {})
        
        # Trích xuất cooking methods từ câu hỏi
        requested_methods = extract_cooking_methods(question)
        
        # Nếu user muốn tất cả các món
        if requested_methods == ["ALL"]:
            return {
                **state,
                "selected_cooking_methods": None,  # None nghĩa là không lọc
                "cooking_request_warning": None,
                "step": "cooking_request_processed"
            }
        
        if not requested_methods:
            # Nếu không nhận diện được cooking method, fallback sang trả về tất cả các món
            return {
                **state,
                "selected_cooking_methods": None,
                "cooking_request_warning": None,
                "step": "cooking_request_processed"
            }
        
        # Kiểm tra tính phù hợp với bệnh
        medical_conditions = [c for c in user_data.get("medicalConditions", []) if c not in ["Không có", "Bình thường"]]
        suitable_methods = []
        unsuitable_methods = []
        warning_messages = []
        
        for method in requested_methods:
            is_suitable = True
            
            # Kiểm tra từng bệnh
            for condition in medical_conditions:
                disease_methods = GraphSchemaService.get_cook_methods_by_disease(condition)
                if disease_methods and method not in disease_methods:
                    is_suitable = False
                    warning_messages.append(f"Phương pháp '{method}' có thể không phù hợp với tình trạng '{condition}' của bạn")
            
            if is_suitable:
                suitable_methods.append(method)
            else:
                unsuitable_methods.append(method)
        
        # Tạo message cảnh báo nếu có
        warning_message = ""
        if warning_messages:
            warning_message = " | ".join(warning_messages)
        
        # Cập nhật state
        updated_state = {
            **state,
            "selected_cooking_methods": suitable_methods + unsuitable_methods,  # Bao gồm cả phù hợp và không phù hợp
            "cooking_request_warning": warning_message if warning_message else None,
            "step": "cooking_request_processed"
        }
        
        return updated_state
        
    except Exception as e:
        return {
            **state,
            "error": f"Lỗi xử lý yêu cầu cooking method: {str(e)}",
            "step": "cooking_request_error"
        } 