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

        if not neo4j_result or neo4j_result.get("status") == "error":
            return {"aggregated_result": {"status": "error", "message": neo4j_result.get("message", "Lỗi từ bước truy vấn Neo4j.")}}

        # Xử lý trường hợp fallback từ node trước (không tìm thấy món theo tiêu chí, trả về món phổ biến)
        if neo4j_result.get("status") == "popular_foods":
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

        # Thêm khai báo biến bmi_category và real_conditions
        bmi_category = bmi_result.get("bmi_category", "") if bmi_result else ""
        medical_conditions = user_data.get("medicalConditions", [])
        real_conditions = []
        if medical_conditions:
            for condition in medical_conditions:
                condition_lower = condition.lower().strip()
                if condition_lower not in ["không có", "không bệnh", "không có bệnh", "bình thường", "khỏe mạnh"]:
                    real_conditions.append(condition)

        # Nếu selected_cooking_methods là None, trả về tất cả các món (trừ previous_food_ids)
        if selected_cooking_methods is None:
            all_foods = []
            for key, value in foods_from_neo4j.items():
                foods = value.get("advanced", [])
                all_foods.extend(foods)
            filtered_final_foods = [
                food for food in all_foods
                if food.get('dish_id') not in previous_food_ids and food.get('id') not in previous_food_ids
            ]
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
                "criteria_used": ["all"]
            }
            return {"aggregated_result": result}

        # Nếu user không có bệnh, không có BMI, và chọn tất cả các phương pháp nấu, trả về tất cả món ăn phù hợp với các phương pháp nấu đó
        if not real_conditions and not bmi_category:
            from app.services.graph_schema_service import GraphSchemaService
            all_foods = GraphSchemaService.get_all_foods_for_healthy_person()
            # Debug log cook_method thực tế
            print("Cook methods in all_foods:", set(food.get('cook_method') for food in all_foods))
            print("Selected methods:", selected_cooking_methods)
            # Nếu user chọn phương pháp nấu cụ thể, filter theo cook_method (không phân biệt hoa thường, bỏ 'Không xác định')
            if selected_cooking_methods:
                selected_methods_lower = [m.lower() for m in selected_cooking_methods]
                all_foods = [food for food in all_foods if food.get('cook_method', '').lower() in selected_methods_lower and food.get('cook_method', '').lower() != 'không xác định']
            filtered_final_foods = [
                food for food in all_foods
                if food.get('dish_id') not in previous_food_ids and food.get('id') not in previous_food_ids
            ]
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
                "criteria_used": ["all"]
            }
            return {"aggregated_result": result}

        # Nếu user đã chỉ định phương pháp nấu, chỉ trả về món đúng phương pháp, không trả về món phương pháp khác
        # Fallback sẽ bỏ lần lượt context, rồi BMI, rồi bệnh nếu không có món phù hợp
        # 1. Lọc giao cả 3 tiêu chí (bệnh, BMI, phương pháp) + giữ đúng phương pháp nấu
        def filter_by_cooking_and_diet(foods, methods, diet=None):
            # Lọc đúng phương pháp nấu, nếu có diet thì lọc thêm diet
            result = [food for food in foods if food.get('cook_method') in methods]
            if diet:
                result = [food for food in result if food.get('diet_name', '').lower() == diet.lower()]
            return result

        # Lấy diet nếu user hỏi món chay, món nước chay, xào chay, ...
        user_question = state.get('question', '').lower()
        diet_filter = None
        if 'chay' in user_question:
            diet_filter = 'chay'
        # Có thể mở rộng thêm các chế độ ăn khác nếu cần

        # 1. Giao cả 3 tiêu chí
        foods_intersection = aggregate_foods_by_intersection(
            bmi_foods, cooking_foods, disease_foods, 
            bmi_category, selected_cooking_methods, real_conditions,
            previous_food_ids
        )
        filtered_final_foods = filter_by_cooking_and_diet(foods_intersection, selected_cooking_methods, diet_filter)
        if filtered_final_foods:
            result = {
                "status": "success",
                "message": f"Tìm thấy {len(filtered_final_foods)} món ăn phù hợp",
                "aggregated_foods": filtered_final_foods,
                "criteria_used": neo4j_result.get("conditions_checked", []) + neo4j_result.get("bmi_checked", []) + neo4j_result.get("cooking_methods_checked", [])
            }
            return {"aggregated_result": result}
        # 2. Bỏ context (chỉ lấy giao BMI, bệnh, phương pháp)
        # (Ở đây context đã được áp dụng ở bước truy vấn, nên không cần bỏ thêm)
        # 3. Bỏ BMI (chỉ lấy giao bệnh và phương pháp)
        foods_no_bmi = aggregate_foods_by_intersection(
            [], cooking_foods, disease_foods, '', selected_cooking_methods, real_conditions, previous_food_ids
        )
        filtered_no_bmi = filter_by_cooking_and_diet(foods_no_bmi, selected_cooking_methods, diet_filter)
        if filtered_no_bmi:
            result = {
                "status": "success",
                "message": f"Tìm thấy {len(filtered_no_bmi)} món ăn phù hợp (bỏ lọc BMI)",
                "aggregated_foods": filtered_no_bmi,
                "criteria_used": neo4j_result.get("conditions_checked", []) + neo4j_result.get("cooking_methods_checked", [])
            }
            return {"aggregated_result": result}
        # 4. Bỏ luôn cả BMI và bệnh (chỉ lấy theo phương pháp)
        filtered_cooking_only = filter_by_cooking_and_diet(cooking_foods, selected_cooking_methods, diet_filter)
        if filtered_cooking_only:
            result = {
                "status": "success",
                "message": f"Tìm thấy {len(filtered_cooking_only)} món ăn phù hợp (chỉ theo phương pháp nấu)",
                "aggregated_foods": filtered_cooking_only,
                "criteria_used": neo4j_result.get("cooking_methods_checked", [])
            }
            return {"aggregated_result": result}
        # 5. Nếu vẫn không có, kiểm tra xem có phải request món chay không
        user_question = state.get('question', '').lower()
        if 'chay' in user_question:
            print("DEBUG: No foods found but user asked for vegetarian, filtering by name...")
            # Lấy tất cả món ăn và filter bằng tên
            try:
                from app.services.graph_schema_service import GraphSchemaService
                all_foods = GraphSchemaService.get_all_foods_for_healthy_person()
                
                # Filter món chay bằng từ khóa trong tên
                vegetarian_keywords = ['rau', 'củ', 'đậu', 'nấm', 'cháo', 'chè', 'bánh', 'sinh tố', 'salad', 'gỏi', 'canh', 'súp', 'cơm', 'bún', 'phở', 'mì']
                meat_keywords = ['thịt', 'cá', 'gà', 'vịt', 'bò', 'heo', 'tôm', 'cua', 'mực', 'ốc', 'sò', 'trứng', 'lươn', 'bạch tuộc', 'hải sản']
                
                vegetarian_foods = []
                for food in all_foods:
                    dish_name = food.get('dish_name', '').lower()
                    has_meat = any(meat_word in dish_name for meat_word in meat_keywords)
                    has_veg = any(veg_word in dish_name for veg_word in vegetarian_keywords)
                    
                    if not has_meat and (has_veg or 'chay' in dish_name):
                        vegetarian_foods.append(food)
                
                # Lọc trừ previous_food_ids
                filtered_vegetarian = [food for food in vegetarian_foods if food.get('dish_id') not in previous_food_ids]
                
                if filtered_vegetarian:
                    print(f"DEBUG: Found {len(filtered_vegetarian)} vegetarian foods by name filtering")
                    return {"aggregated_result": {
                        "status": "success",
                        "message": f"Tìm thấy {len(filtered_vegetarian)} món chay từ cơ sở dữ liệu",
                        "aggregated_foods": filtered_vegetarian
                    }}
                else:
                    print("DEBUG: No vegetarian foods found by name filtering")
            except Exception as e:
                print(f"DEBUG: Vegetarian filtering failed: {e}")
        
        # Nếu không phải món chay hoặc filter fail, trả về empty
        return {"aggregated_result": {
            "status": "empty",
            "message": "Không có món ăn nào phù hợp với yêu cầu của bạn.",
            "aggregated_foods": []
        }}
        
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
    
    # Xác định tiêu chí nào có sẵn
    has_bmi = bool(bmi_category and bmi_ids)
    has_cooking = bool(cooking_methods and cooking_ids)
    has_disease = bool(diseases and disease_ids)
    
    # Đặc biệt xử lý trường hợp có 0 bệnh (không có bệnh thực sự)
    # Trong trường hợp này, chúng ta không nên lọc theo bệnh
    if diseases == []:  # Không có bệnh thực sự
        has_disease = False
    
    # Lấy intersection dựa trên tiêu chí có sẵn
    if has_bmi and has_cooking and has_disease:
        # Có đủ 3 tiêu chí: lấy giao của cả 3
        final_ids = bmi_ids & cooking_ids & disease_ids
        
    elif has_bmi and has_cooking:
        # Có BMI và cách chế biến: lấy giao của 2
        final_ids = bmi_ids & cooking_ids
        
    elif has_bmi and has_disease:
        # Có BMI và bệnh: lấy giao của 2
        final_ids = bmi_ids & disease_ids
        
    elif has_cooking and has_disease:
        # Có cách chế biến và bệnh: lấy giao của 2
        final_ids = cooking_ids & disease_ids
        
    elif has_bmi:
        # Chỉ có BMI: lấy tất cả món ăn theo BMI
        final_ids = bmi_ids
        
    elif has_cooking:
        # Chỉ có cách chế biến: lấy tất cả món ăn theo cách chế biến
        final_ids = cooking_ids
        
    elif has_disease:
        # Chỉ có bệnh: lấy tất cả món ăn theo bệnh
        final_ids = disease_ids
        
    else:
        # Không có tiêu chí nào: trả về món ăn phổ biến
        try:
            popular_foods = GraphSchemaService.get_popular_foods(excluded_ids=excluded_ids)
            return popular_foods
        except Exception as e:
            return []
    
    # Tạo danh sách món ăn cuối cùng từ final_ids
    all_foods = bmi_foods + cooking_foods + disease_foods
    
    final_foods = []
    matched_count = 0
    
    for food in all_foods:
        food_id = food.get("dish_id")
        if food_id in final_ids:
            matched_count += 1
            # Kiểm tra xem đã có trong final_foods chưa để tránh trùng lặp
            if not any(f.get("dish_id") == food_id for f in final_foods):
                final_foods.append(food)
    
    return final_foods 