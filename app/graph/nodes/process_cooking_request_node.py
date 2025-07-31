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
        allowed_methods = set()
        for condition in medical_conditions:
            allowed_methods.update(GraphSchemaService.get_cook_methods_by_disease(condition))
        if not allowed_methods:
            allowed_methods = set(GraphSchemaService.get_all_cooking_methods())

        # Lọc các phương pháp phù hợp và không phù hợp
        suitable_methods = [m for m in requested_methods if m in allowed_methods]
        unsuitable_methods = [m for m in requested_methods if m not in allowed_methods]

        warning_message = None
        if unsuitable_methods:
            warning_message = (
                f"phương pháp nấu không phù hợp với tình trạng bệnh của bạn và đã bị loại bỏ: {', '.join(unsuitable_methods)}"
            )

        # Nếu không còn phương pháp nào phù hợp, có thể trả về lỗi hoặc yêu cầu chọn lại
        if not suitable_methods:
            return {
                **state,
                "selected_cooking_methods": [],
                "cooking_request_warning": warning_message or "Không có phương pháp nấu nào phù hợp với tình trạng bệnh của bạn.",
                "step": "cooking_request_processed"
            }

        # Cập nhật state
        return {
            **state,
            "selected_cooking_methods": suitable_methods,
            "cooking_request_warning": warning_message,
            "step": "cooking_request_processed"
        }
        
    except Exception as e:
        return {
            **state,
            "error": f"Lỗi xử lý yêu cầu cooking method: {str(e)}",
            "step": "cooking_request_error"
        } 