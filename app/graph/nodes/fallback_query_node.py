from typing import Dict, Any, List

def create_fallback_query(user_context: Dict[str, Any], attempt: int = 1) -> Dict[str, Any]:
    """
    Tạo query fallback đơn giản hơn khi LLM trả về "no"
    
    Args:
        user_context: Thông tin người dùng
        attempt: Lần thử thứ mấy (1: bỏ cảm xúc, 2: bỏ cảm xúc + chế độ ăn)
        
    Returns:
        Dict chứa query fallback
    """
    try:
        medical_conditions = user_context.get("medical_conditions", [])
        bmi_category = user_context.get("bmi_category", "")
        
        # Query cơ bản chỉ dựa trên bệnh lý
        base_query = """
        MATCH (d:Disease)-[:KHUYẾN_NGHỊ]->(di:Diet)-[:ĐƯỢC_DÙNG_TRONG]->(dish:Dish)
        WHERE d.name IN $conditions
        WITH dish, di, d
        OPTIONAL MATCH (dish)-[:ĐƯỢC_CHẾ_BIẾN_BẰNG]->(cm:CookMethod)
        RETURN DISTINCT 
            dish.name as dish_name,
            dish.description as dish_description,
            di.name as diet_name,
            di.description as diet_description,
            COALESCE(cm.name, 'Không xác định') as cook_method,
            d.name as disease_name
        ORDER BY dish.name
        """
        
        # Query fallback level 1: bỏ cảm xúc, giữ chế độ ăn
        if attempt == 1:
            query = base_query
            params = {"conditions": medical_conditions}
            
        # Query fallback level 2: bỏ cảm xúc và chế độ ăn, chỉ giữ bệnh lý
        elif attempt == 2:
            query = """
            MATCH (d:Disease)-[:KHUYẾN_NGHỊ]->(di:Diet)-[:ĐƯỢC_DÙNG_TRONG]->(dish:Dish)
            WHERE d.name IN $conditions
            WITH dish, di, d
            OPTIONAL MATCH (dish)-[:ĐƯỢC_CHẾ_BIẾN_BẰNG]->(cm:CookMethod)
            RETURN DISTINCT 
                dish.name as dish_name,
                dish.description as dish_description,
                di.name as diet_name,
                di.description as diet_description,
                COALESCE(cm.name, 'Không xác định') as cook_method,
                d.name as disease_name
            ORDER BY dish.name
            LIMIT 20
            """
            params = {"conditions": medical_conditions}
            
        # Query fallback level 3: chỉ lấy tất cả món ăn
        else:
            query = """
            MATCH (dish:Dish)
            OPTIONAL MATCH (dish)-[:ĐƯỢC_DÙNG_TRONG]-(di:Diet)
            OPTIONAL MATCH (dish)-[:ĐƯỢC_CHẾ_BIẾN_BẰNG]->(cm:CookMethod)
            RETURN DISTINCT 
                dish.name as dish_name,
                dish.description as dish_description,
                COALESCE(di.name, 'Không xác định') as diet_name,
                COALESCE(di.description, '') as diet_description,
                COALESCE(cm.name, 'Không xác định') as cook_method,
                'Tất cả món ăn' as disease_name
            ORDER BY dish.name
            LIMIT 15
            """
            params = {}
        
        return {
            "status": "success",
            "query": query,
            "params": params,
            "attempt": attempt,
            "message": f"Đã tạo query fallback level {attempt}",
            "filters_applied": {
                "medical_conditions": medical_conditions if attempt < 3 else [],
                "bmi_category": bmi_category if attempt < 2 else "",
                "emotion": "" if attempt >= 1 else user_context.get("emotion", "")
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Lỗi tạo query fallback: {str(e)}",
            "query": "",
            "params": {},
            "attempt": attempt
        } 