from app.services.graph_schema_service import GraphSchemaService
from typing import Dict, Any, List, Set

def aggregate_suitable_foods(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node tổng hợp các món ăn từ kết quả của node query_neo4j.
    Nó không thực hiện truy vấn mới mà chỉ xử lý dữ liệu đã có.
    """
    try:
        neo4j_result = state.get("neo4j_result", {})
        previous_food_ids = state.get("previous_food_ids", [])

        print("DEBUG: neo4j_result foods keys:", list(neo4j_result.get("foods", {}).keys()))
        print("DEBUG: previous_food_ids:", previous_food_ids)
        for k, v in neo4j_result.get("foods", {}).items():
            print(f"DEBUG: {k} - {len(v.get('advanced', []))} món")
            for food in v.get('advanced', []):
                if food.get('dish_id') in previous_food_ids:
                    print("!!! FOUND DUPLICATE:", food.get('dish_name'), food.get('dish_id'))

        if not neo4j_result or neo4j_result.get("status") == "error":
            return {"aggregated_result": {"status": "error", "message": neo4j_result.get("message", "Lỗi từ bước truy vấn Neo4j.")}}

        # Xử lý trường hợp fallback từ node trước (không tìm thấy món theo tiêu chí, trả về món phổ biến)
        if neo4j_result.get("status") == "popular_foods":
            print("DEBUG: [aggregate_foods] Processing popular foods from neo4j_result.")
            popular_foods = neo4j_result.get("foods", {}).get("popular", {}).get("advanced", [])
            # Lọc lại một lần nữa để đảm bảo không có món cũ
            filtered_popular = [food for food in popular_foods if food.get('dish_id') not in previous_food_ids]
            if not filtered_popular:
                return {"aggregated_result": {
                    "status": "empty",
                    "message": "Không còn món ăn phù hợp nào khác để gợi ý.",
                    "aggregated_foods": []
                }}
            return {"aggregated_result": {
                "status": "success",
                "message": f"Tìm thấy {len(filtered_popular)} món ăn phổ biến.",
                "aggregated_foods": filtered_popular,
                "criteria_used": {"source": "popular"}
            }}

        # Trích xuất các danh sách món ăn từ kết quả của Neo4j
        foods_from_neo4j = neo4j_result.get("foods", {})
        bmi_foods = []
        cooking_foods = []
        disease_foods = []

        for key, value in foods_from_neo4j.items():
            source = value.get("source")
            foods = value.get("advanced", [])
            if source == "bmi":
                bmi_foods.extend(foods)
            elif source == "cooking_method":
                cooking_foods.extend(foods)
            elif source == "medical_condition":
                disease_foods.extend(foods)
        
        # Lấy lại các tiêu chí đã sử dụng để đưa vào hàm tổng hợp
        user_data = state.get("user_data", {})
        bmi_result = state.get("bmi_result", {})
        selected_cooking_methods = state.get("selected_cooking_methods", [])
        
        bmi_category = bmi_result.get("bmi_category", "") if bmi_result else ""
        medical_conditions = user_data.get("medicalConditions", [])
        
        real_conditions = []
        if medical_conditions:
            for condition in medical_conditions:
                condition_lower = condition.lower().strip()
                if condition_lower not in ["không có", "không bệnh", "không có bệnh", "bình thường", "khỏe mạnh"]:
                    real_conditions.append(condition)

        # Tổng hợp các món ăn bằng logic giao/hợp
        final_foods = aggregate_foods_by_intersection(
            bmi_foods, cooking_foods, disease_foods, 
            bmi_category, selected_cooking_methods, real_conditions,
            previous_food_ids  # Truyền danh sách loại trừ vào hàm fallback
        )
        
        print(f"DEBUG: Final aggregated foods count: {len(final_foods)}")

        # Lọc lại một lần nữa để đảm bảo không có món cũ
        filtered_final_foods = [food for food in final_foods if food.get('dish_id') not in previous_food_ids]
        print("DEBUG: previous_food_ids:", previous_food_ids)
        print("DEBUG: dish_ids in filtered_final_foods:", [food.get('dish_id') for food in filtered_final_foods])
        for food in filtered_final_foods:
            if food.get('dish_id') in previous_food_ids:
                print("!!! STILL DUPLICATE IN FINAL:", food.get('dish_name'), food.get('dish_id'))
                raise Exception(f"Duplicate dish_id found in final result: {food.get('dish_id')}")
        if not filtered_final_foods:
            return {"aggregated_result": {
                "status": "empty",
                "message": "Không còn món ăn phù hợp nào khác để gợi ý.",
                "aggregated_foods": []
            }}

        result = {
            "status": "success",
            "message": f"Tìm thấy {len(filtered_final_foods)} món ăn phù hợp",
            "aggregated_foods": filtered_final_foods,
            "criteria_used": neo4j_result.get("conditions_checked", []) + neo4j_result.get("bmi_checked", []) + neo4j_result.get("cooking_methods_checked", [])
        }
        
        return {"aggregated_result": result}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"aggregated_result": {"status": "error", "message": str(e)}}

def aggregate_foods_by_intersection(bmi_foods: List[Dict], cooking_foods: List[Dict], 
                                  disease_foods: List[Dict], bmi_category: str, 
                                  cooking_methods: List[str], diseases: List[str],
                                  excluded_ids: List[str] = None) -> List[Dict]:
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
            popular_foods = GraphSchemaService.get_popular_foods(limit=20, excluded_ids=excluded_ids)
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