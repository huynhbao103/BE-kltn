from app.services.graph_schema_service import GraphSchemaService
from typing import Dict, Any, List, Set

def aggregate_suitable_foods(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node tổng hợp các món ăn phù hợp theo BMI, cách chế biến và bệnh
    """
    try:
        user_data = state.get("user_data", {})
        bmi_result = state.get("bmi_result", {})
        selected_cooking_methods = state.get("selected_cooking_methods", [])
        
        # Lấy thông tin từ state
        bmi_category = bmi_result.get("bmi_category", "") if bmi_result else ""
        medical_conditions = user_data.get("medicalConditions", [])
        
        print(f"DEBUG: Aggregating foods for:")
        print(f"  - BMI: {bmi_category}")
        print(f"  - Cooking methods: {selected_cooking_methods}")
        print(f"  - Medical conditions: {medical_conditions}")
        
        # Kiểm tra có bệnh thực sự hay không
        real_conditions = []
        if medical_conditions:
            for condition in medical_conditions:
                condition_lower = condition.lower().strip()
                if condition_lower not in ["không có", "không bệnh", "không có bệnh", "bình thường", "khỏe mạnh"]:
                    real_conditions.append(condition)
        
        # Các danh sách món ăn theo từng tiêu chí
        bmi_foods = []
        cooking_foods = []
        disease_foods = []
        
        # 1. Lấy món ăn theo BMI
        if bmi_category and bmi_category.strip():
            try:
                print(f"DEBUG: Querying foods for BMI: {bmi_category}")
                bmi_foods = GraphSchemaService.get_foods_by_bmi(bmi_category.lower())
                print(f"DEBUG: Found {len(bmi_foods)} foods for BMI")
            except Exception as e:
                print(f"Error querying BMI foods: {e}")
        
        # 2. Lấy món ăn theo cách chế biến
        if selected_cooking_methods and len(selected_cooking_methods) > 0:
            for method in selected_cooking_methods:
                try:
                    print(f"DEBUG: Querying foods for cooking method: {method}")
                    method_foods = GraphSchemaService.get_foods_by_cooking_method(method)
                    print(f"DEBUG: Found {len(method_foods)} foods for method {method}")
                    cooking_foods.extend(method_foods)
                except Exception as e:
                    print(f"Error querying cooking method foods: {e}")
        
        # 3. Lấy món ăn theo bệnh
        if real_conditions:
            for condition in real_conditions:
                try:
                    print(f"DEBUG: Querying foods for disease: {condition}")
                    condition_foods = GraphSchemaService.get_foods_by_disease_advanced(condition)
                    print(f"DEBUG: Found {len(condition_foods)} foods for disease {condition}")
                    disease_foods.extend(condition_foods)
                except Exception as e:
                    print(f"Error querying disease foods: {e}")
        
        # Tổng hợp các món ăn
        final_foods = aggregate_foods_by_intersection(bmi_foods, cooking_foods, disease_foods, 
                                                     bmi_category, selected_cooking_methods, real_conditions)
        
        print(f"DEBUG: Final aggregated foods count: {len(final_foods)}")
        print(f"DEBUG: Final foods sample: {final_foods[:3] if final_foods else 'No foods'}")
        
        result = {
            "status": "success",
            "message": f"Tìm thấy {len(final_foods)} món ăn phù hợp",
            "aggregated_foods": final_foods,
            "criteria_used": {
                "bmi": bmi_category if bmi_category else None,
                "cooking_methods": selected_cooking_methods,
                "diseases": real_conditions
            },
            "food_counts": {
                "bmi_foods": len(bmi_foods),
                "cooking_foods": len(cooking_foods),
                "disease_foods": len(disease_foods),
                "final_foods": len(final_foods)
            }
        }
        
        # Trả về chỉ phần thay đổi của state theo quy tắc LangGraph
        return {"aggregated_result": result}
        
    except Exception as e:
        return {"aggregated_result": {"status": "error", "message": str(e)}}

def aggregate_foods_by_intersection(bmi_foods: List[Dict], cooking_foods: List[Dict], 
                                  disease_foods: List[Dict], bmi_category: str, 
                                  cooking_methods: List[str], diseases: List[str]) -> List[Dict]:
    """
    Tổng hợp món ăn bằng cách lấy giao (intersection) của các tiêu chí
    """
    # Chuyển đổi thành sets để dễ xử lý intersection
    bmi_ids = {food.get("dish_id") for food in bmi_foods if food.get("dish_id")}
    cooking_ids = {food.get("dish_id") for food in cooking_foods if food.get("dish_id")}
    disease_ids = {food.get("dish_id") for food in disease_foods if food.get("dish_id")}
    
    print(f"DEBUG: Food IDs by criteria:")
    print(f"  - BMI ({bmi_category}): {len(bmi_ids)} foods")
    print(f"  - Cooking methods ({cooking_methods}): {len(cooking_ids)} foods")
    print(f"  - Diseases ({diseases}): {len(disease_ids)} foods")
    
    # Xác định tiêu chí nào có sẵn
    has_bmi = bool(bmi_category and bmi_ids)
    has_cooking = bool(cooking_methods and cooking_ids)
    has_disease = bool(diseases and disease_ids)
    
    # Đặc biệt xử lý trường hợp có 0 bệnh (không có bệnh thực sự)
    # Trong trường hợp này, chúng ta không nên lọc theo bệnh
    if diseases == []:  # Không có bệnh thực sự
        has_disease = False
        print("DEBUG: No real diseases found, skipping disease filtering")
    
    print(f"DEBUG: Criteria availability:")
    print(f"  - has_bmi: {has_bmi} (bmi_category: '{bmi_category}', bmi_ids count: {len(bmi_ids)})")
    print(f"  - has_cooking: {has_cooking} (cooking_methods: {cooking_methods}, cooking_ids count: {len(cooking_ids)})")
    print(f"  - has_disease: {has_disease} (diseases: {diseases}, disease_ids count: {len(disease_ids)})")
    
    # Lấy intersection dựa trên tiêu chí có sẵn
    if has_bmi and has_cooking and has_disease:
        # Có đủ 3 tiêu chí: lấy giao của cả 3
        final_ids = bmi_ids & cooking_ids & disease_ids
        print(f"DEBUG: Using intersection of all 3 criteria: {len(final_ids)} foods")
        
    elif has_bmi and has_cooking:
        # Có BMI và cách chế biến: lấy giao của 2
        final_ids = bmi_ids & cooking_ids
        print(f"DEBUG: Using intersection of BMI and cooking methods: {len(final_ids)} foods")
        
    elif has_bmi and has_disease:
        # Có BMI và bệnh: lấy giao của 2
        final_ids = bmi_ids & disease_ids
        print(f"DEBUG: Using intersection of BMI and diseases: {len(final_ids)} foods")
        
    elif has_cooking and has_disease:
        # Có cách chế biến và bệnh: lấy giao của 2
        final_ids = cooking_ids & disease_ids
        print(f"DEBUG: Using intersection of cooking methods and diseases: {len(final_ids)} foods")
        
    elif has_bmi:
        # Chỉ có BMI: lấy tất cả món ăn theo BMI
        final_ids = bmi_ids
        print(f"DEBUG: Using only BMI criteria: {len(final_ids)} foods")
        
    elif has_cooking:
        # Chỉ có cách chế biến: lấy tất cả món ăn theo cách chế biến
        final_ids = cooking_ids
        print(f"DEBUG: Using only cooking methods criteria: {len(final_ids)} foods")
        
    elif has_disease:
        # Chỉ có bệnh: lấy tất cả món ăn theo bệnh
        final_ids = disease_ids
        print(f"DEBUG: Using only diseases criteria: {len(final_ids)} foods")
        
    else:
        # Không có tiêu chí nào: trả về món ăn phổ biến
        print("DEBUG: No criteria available, returning popular foods")
        try:
            popular_foods = GraphSchemaService.get_popular_foods(limit=20)
            return popular_foods
        except Exception as e:
            print(f"Error getting popular foods: {e}")
            return []
    
    # Debug: Kiểm tra final_ids
    print(f"DEBUG: final_ids count = {len(final_ids)}")
    print(f"DEBUG: final_ids sample = {list(final_ids)[:5] if final_ids else 'Empty'}")
    
    # Tạo danh sách món ăn cuối cùng từ final_ids
    all_foods = bmi_foods + cooking_foods + disease_foods
    print(f"DEBUG: all_foods count = {len(all_foods)}")
    
    final_foods = []
    matched_count = 0
    
    for food in all_foods:
        food_id = food.get("dish_id")
        if food_id in final_ids:
            matched_count += 1
            # Kiểm tra xem đã có trong final_foods chưa để tránh trùng lặp
            if not any(f.get("dish_id") == food_id for f in final_foods):
                final_foods.append(food)
    
    print(f"DEBUG: Matched foods count = {matched_count}")
    print(f"DEBUG: Final unique foods: {len(final_foods)}")
    print(f"DEBUG: Final foods sample: {[f.get('dish_name', 'Unknown') for f in final_foods[:3]] if final_foods else 'No foods'}")
    return final_foods 