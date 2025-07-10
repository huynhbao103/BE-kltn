from typing import Dict, Any, List

def create_fallback_query(user_context: Dict[str, Any], attempt: int = 1) -> Dict[str, Any]:
    """
    Tạo các tham số fallback cho truy vấn tổng hợp khi không tìm thấy kết quả.
    
    Args:
        user_context: Thông tin người dùng và các bộ lọc đã áp dụng
        attempt: Lần thử (1: bỏ cảm xúc, 2: bỏ phương pháp nấu)
        
    Returns:
        Dict chứa các tham số để gọi lại hàm truy vấn chính.
    """
    try:
        # Lấy các bộ lọc đã áp dụng từ lần thử trước
        filters = user_context.get("filters", {})
        conditions = filters.get("medical_conditions", [])
        emotion = filters.get("emotion")
        cooking_methods = filters.get("cooking_methods")

        # Fallback level 1: Bỏ cảm xúc
        if attempt == 1:
            emotion = None
            message = "Thử lại bằng cách bỏ qua bộ lọc cảm xúc."
            
        # Fallback level 2: Bỏ phương pháp nấu
        elif attempt == 2:
            emotion = None
            cooking_methods = None
            message = "Thử lại bằng cách bỏ qua cảm xúc và phương pháp nấu."
            
        # Fallback level 3: Chỉ giữ lại bệnh (nếu có)
        else:
            emotion = None
            cooking_methods = None
            # Giữ lại 'conditions'
            message = "Thử lại chỉ với bộ lọc bệnh lý (nếu có)."

        return {
            "status": "success",
            "message": message,
            "attempt": attempt + 1,
            "fallback_filters": {
                "conditions": conditions,
                "emotion": emotion,
                "cooking_methods": cooking_methods
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Lỗi khi tạo truy vấn fallback: {str(e)}",
            "attempt": attempt
        } 