from app.services.graph_schema_service import GraphSchemaService
from app.services.mongo_service import mongo_service
from app.services.llm.llm_service import LLMService
from typing import Dict, Any, List
import json

def check_dish_name_for_allergies(dish_name: str, user_allergies: List[str]) -> tuple[bool, List[str]]:
    """
    Kiểm tra xem tên món ăn có chứa từ khóa dị ứng không
    Trả về (has_allergic_name, allergic_keywords)
    """
    dish_name_lower = dish_name.lower()
    allergic_keywords = []
    
    for allergy in user_allergies:
        allergy_lower = allergy.lower().strip()
        if allergy_lower in dish_name_lower:
            allergic_keywords.append(allergy)
    
    return len(allergic_keywords) > 0, allergic_keywords

def debug_dish_info(food: Dict[str, Any], mongo_dish: Dict[str, Any] = None) -> None:
    """
    Debug thông tin món ăn để hiểu rõ vấn đề
    """
    dish_name = food.get("name", "Unknown")
    neo4j_id = food.get("neo4j_id")
    ingredients = food.get("ingredients", [])
    
    print(f"[DEBUG] Dish info for {dish_name}:")
    print(f"[DEBUG] - Neo4j ID: {neo4j_id}")
    print(f"[DEBUG] - Ingredients from Neo4j: {ingredients}")
    
    if mongo_dish:
        print(f"[DEBUG] - MongoDB ID: {mongo_dish.get('_id')}")
        print(f"[DEBUG] - Ingredients from MongoDB: {mongo_dish.get('ingredients', [])}")
        print(f"[DEBUG] - Source: {mongo_dish.get('source', 'unknown')}")
    else:
        print(f"[DEBUG] - No MongoDB dish found")

def filter_foods_by_allergies(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Lọc món ăn theo dị ứng của người dùng sử dụng LLM
    """
    try:
        user_data = state.get("user_data", {})
        query_result = state.get("query_result", {})
        user_allergies = user_data.get("allergies", [])
        
        print(f"[DEBUG] Starting allergy filtering for user with allergies: {user_allergies}")
        
        if not user_allergies:
            # Nếu không có dị ứng, trả về kết quả gốc
            print("[DEBUG] No allergies found, returning original result")
            return {"filtered_result": query_result}
        
        # Lấy món ăn từ query_result
        foods = query_result.get("foods", {})
        filtered_foods = {}
        allergy_warnings = {}
        removed_foods = {}  # Để track các món bị loại bỏ
        
        print(f"[DEBUG] Processing {len(foods)} food sources")
        
        for source_key, food_data in foods.items():
            advanced_foods = food_data.get("advanced", [])
            print(f"[DEBUG] Processing source {source_key} with {len(advanced_foods)} foods")
            
            filtered_advanced = []
            
            for food in advanced_foods:
                dish_name = food.get("name", "Unknown dish")
                print(f"[DEBUG] Processing dish: {dish_name}")
                
                # Kiểm tra tên món ăn trước - nếu tên chứa từ khóa dị ứng, loại bỏ ngay
                has_allergic_name, allergic_keywords = check_dish_name_for_allergies(dish_name, user_allergies)
                
                if has_allergic_name:
                    print(f"[DEBUG] REMOVING {dish_name} - name contains allergic keywords: {allergic_keywords}")
                    # Loại bỏ món ăn có tên chứa từ khóa dị ứng
                    if source_key not in removed_foods:
                        removed_foods[source_key] = []
                    removed_foods[source_key].append({
                        "dish_name": dish_name,
                        "reason": f"Tên món ăn chứa từ khóa dị ứng: {', '.join(allergic_keywords)}",
                        "allergic_keywords": allergic_keywords
                    })
                    continue
                
                # Lấy thông tin đầy đủ từ MongoDB nếu có neo4j_id
                neo4j_id = food.get("neo4j_id")
                mongo_dish = None
                
                if neo4j_id:
                    # Tìm món ăn trong MongoDB theo neo4j_id
                    mongo_dishes = mongo_service.get_all_dishes()
                    for dish in mongo_dishes:
                        if dish.get("neo4j_id") == neo4j_id:
                            mongo_dish = dish
                            break
                
                # Debug thông tin món ăn
                debug_dish_info(food, mongo_dish)
                
                # Sử dụng thông tin từ MongoDB nếu có, không thì dùng từ Neo4j
                dish_ingredients = []
                if mongo_dish and mongo_dish.get("ingredients"):
                    dish_ingredients = mongo_dish.get("ingredients", [])
                    print(f"[DEBUG] Found ingredients from MongoDB for {dish_name}: {dish_ingredients}")
                else:
                    # Fallback: lấy ingredients từ Neo4j nếu có
                    dish_ingredients = food.get("ingredients", [])
                    print(f"[DEBUG] Using ingredients from Neo4j for {dish_name}: {dish_ingredients}")
                
                # Nếu không có ingredients, sử dụng tên món ăn để kiểm tra dị ứng
                if not dish_ingredients:
                    print(f"[DEBUG] No ingredients found for {dish_name}, checking dish name only")
                    # Kiểm tra tên món ăn có chứa từ khóa gây dị ứng không
                    has_allergic_ingredient, allergic_keywords = check_dish_name_for_allergies(dish_name, user_allergies)
                    
                    if has_allergic_ingredient:
                        print(f"[DEBUG] REMOVING {dish_name} - name contains allergic keywords: {allergic_keywords}")
                        # Loại bỏ món ăn có tên chứa từ khóa dị ứng
                        if source_key not in removed_foods:
                            removed_foods[source_key] = []
                        removed_foods[source_key].append({
                            "dish_name": dish_name,
                            "reason": f"Tên món ăn chứa từ khóa dị ứng (không có ingredients): {', '.join(allergic_keywords)}",
                            "allergic_keywords": allergic_keywords
                        })
                        continue
                    else:
                        print(f"[DEBUG] Adding {dish_name} to safe list (no ingredients, safe name)")
                        # Nếu không có ingredients và tên không chứa từ khóa dị ứng, thêm vào danh sách an toàn
                        # nhưng với cảnh báo
                        food["allergy_analysis"] = {
                            "is_safe": True,
                            "main_ingredients": [],
                            "side_ingredients": [],
                            "allergic_ingredients": [],
                            "warnings": ["Không có thông tin ingredients đầy đủ, chỉ kiểm tra dựa trên tên món ăn"],
                            "reasoning": "Món ăn được coi là an toàn dựa trên tên, nhưng cần kiểm tra thêm ingredients"
                        }
                        filtered_advanced.append(food)
                        continue
                
                # Sử dụng LLM để phân tích nguyên liệu chính/phụ
                analysis_result = analyze_ingredients_with_llm(
                    dish_ingredients, 
                    user_allergies,
                    dish_name
                )
                
                # Thêm thông tin phân tích vào food
                food["allergy_analysis"] = analysis_result
                if mongo_dish:
                    # Merge thông tin từ MongoDB
                    food.update({
                        "mongo_id": mongo_dish.get("_id"),
                        "full_ingredients": mongo_dish.get("ingredients", []),
                        "instructions": mongo_dish.get("instructions", []),
                        "source": mongo_dish.get("source", "neo4j_migration")
                    })
                
                # Chỉ thêm món ăn an toàn vào danh sách
                if analysis_result["is_safe"]:
                    filtered_advanced.append(food)
                else:
                    # Track món ăn bị loại bỏ
                    if source_key not in removed_foods:
                        removed_foods[source_key] = []
                    removed_foods[source_key].append({
                        "dish_name": dish_name,
                        "reason": f"Chứa nguyên liệu gây dị ứng: {', '.join(analysis_result.get('allergic_ingredients', []))}",
                        "allergic_ingredients": analysis_result.get('allergic_ingredients', [])
                    })
                
                # Thêm cảnh báo nếu có (chỉ cho món an toàn có nguyên liệu phụ gây dị ứng)
                if analysis_result.get("warnings") and analysis_result["is_safe"]:
                    if source_key not in allergy_warnings:
                        allergy_warnings[source_key] = []
                    allergy_warnings[source_key].append({
                        "dish_name": dish_name,
                        "warnings": analysis_result["warnings"]
                    })
            
            if filtered_advanced:
                filtered_foods[source_key] = {
                    **food_data,
                    "advanced": filtered_advanced
                }
        
        # Cập nhật kết quả
        filtered_result = {
            **query_result,
            "foods": filtered_foods,
            "allergy_warnings": allergy_warnings,
            "removed_foods": removed_foods,  # Thêm thông tin về các món bị loại bỏ
            "original_food_count": sum(len(food_data.get("advanced", [])) for food_data in foods.values()),
            "filtered_food_count": sum(len(food_data.get("advanced", [])) for food_data in filtered_foods.values()),
            "user_allergies": user_allergies
        }
        
        print(f"[DEBUG] Allergy filtering complete:")
        print(f"[DEBUG] - Original food count: {filtered_result['original_food_count']}")
        print(f"[DEBUG] - Filtered food count: {filtered_result['filtered_food_count']}")
        print(f"[DEBUG] - Removed foods: {removed_foods}")
        print(f"[DEBUG] - Allergy warnings: {allergy_warnings}")
        
        return {"filtered_result": filtered_result}
        
    except Exception as e:
        print(f"Error in filter_foods_by_allergies: {e}")
        return {
            "filtered_result": query_result,
            "error": f"Lỗi lọc dị ứng: {str(e)}"
        }

def analyze_ingredients_with_llm(ingredients: List[str], user_allergies: List[str], dish_name: str) -> Dict[str, Any]:
    """
    Sử dụng LLM để phân tích nguyên liệu và kiểm tra dị ứng
    """
    try:
        # Tạo prompt cho LLM
        prompt = f"""
        Phân tích món ăn "{dish_name}" với các nguyên liệu: {', '.join(ingredients)}
        
        Danh sách dị ứng của người dùng: {', '.join(user_allergies)}
        
        Hãy phân tích và trả về kết quả theo format JSON sau:
        {{
            "is_safe": true/false,
            "main_ingredients": ["danh sách nguyên liệu chính"],
            "side_ingredients": ["danh sách nguyên liệu phụ"],
            "allergic_ingredients": ["nguyên liệu gây dị ứng nếu có"],
            "warnings": ["cảnh báo nếu có"],
            "reasoning": "giải thích ngắn gọn"
        }}
        
        QUY TẮC PHÂN LOẠI NGUYÊN LIỆU:
        1. NGUYÊN LIỆU CHÍNH (main_ingredients): thịt, cá, tôm, cua, gà, vịt, bò, heo, trứng, đậu, cơm, bún, phở, mì, bánh, rau chính, khoai, sắn, ngô, đậu phộng, lạc, hạt điều, hạnh nhân, ếch, lươn, ốc, sò, bạch tuộc, mực, tôm hùm, cua biển, cá hồi, cá thu, cá ngừ, cá trê, cá lóc, cá rô, cá chép, cá trắm, cá mè, cá trôi, cá chạch, cá bống, cá bớp, cá đối, cá kèo, cá linh, cá lăng, cá nheo, cá quả, cá trắng, cá đen, cá vàng, cá xanh, cá đỏ, cá tím, cá cam, cá hồng, cá xám, cá nâu, cá đen, cá trắng, cá vàng, cá xanh, cá đỏ, cá tím, cá cam, cá hồng, cá xám, cá nâu
        
        2. NGUYÊN LIỆU PHỤ (side_ingredients): hành, tỏi, gừng, nghệ, ớt, tiêu, muối, đường, nước mắm, dầu, mỡ, bơ, sữa, kem, bột, rau thơm, ngò, húng, tía tô, kinh giới, hành lá, ngò gai, tôm khô, cá khô, mắm, dầu ăn, mỡ heo, rau răm, rau mùi, rau húng, rau tía tô, rau kinh giới, rau húng quế, rau húng chó, rau húng lủi, rau húng cây, rau húng chanh, rau húng quế, rau húng chó, rau húng lủi, rau húng cây, rau húng chanh
        
        QUY TẮC AN TOÀN:
        3. Nếu có nguyên liệu CHÍNH gây dị ứng -> is_safe = false (LOẠI BỎ MÓN ĂN)
        4. Nếu chỉ có nguyên liệu PHỤ gây dị ứng -> is_safe = true, thêm warning (CẢNH BÁO)
        5. Nếu không có nguyên liệu gây dị ứng -> is_safe = true
        
        LƯU Ý ĐẶC BIỆT:
        - Ếch, lươn, ốc, sò, bạch tuộc, mực, tôm, cua, cá là nguyên liệu CHÍNH, không phải phụ!
        - Nếu tên món ăn chứa từ khóa dị ứng (như "Ếch Kho Rau Răm" có "ếch"), thì món ăn đó KHÔNG AN TOÀN
        - Rau răm, rau mùi, rau húng là nguyên liệu PHỤ
        
        Trả về JSON hợp lệ.
        """
        
        # Gọi LLM
        llm_response = LLMService.get_completion(prompt)
        
        # Parse JSON response
        try:
            analysis = json.loads(llm_response)
            print(f"[DEBUG] LLM response for {dish_name}: {analysis}")
            return analysis
        except json.JSONDecodeError:
            print(f"[DEBUG] LLM JSON parse error for {dish_name}, using fallback")
            # Fallback: phân tích đơn giản không dùng LLM
            return fallback_ingredient_analysis(ingredients, user_allergies, dish_name)
            
    except Exception as e:
        print(f"Error in analyze_ingredients_with_llm: {e}")
        # Fallback: phân tích đơn giản không dùng LLM
        return fallback_ingredient_analysis(ingredients, user_allergies, dish_name)

def fallback_ingredient_analysis(ingredients: List[str], user_allergies: List[str], dish_name: str) -> Dict[str, Any]:
    """
    Phân tích đơn giản khi LLM không khả dụng
    """
    # Danh sách nguyên liệu chính thường gặp (mở rộng)
    main_ingredients_keywords = [
        "thịt", "cá", "tôm", "cua", "gà", "vịt", "bò", "heo", "lợn", "trứng", "đậu",
        "cơm", "bún", "phở", "mì", "bánh", "rau", "cải", "bắp cải", "su hào", "cà rốt",
        "khoai", "sắn", "ngô", "bắp", "đậu phộng", "lạc", "hạt điều", "hạnh nhân",
        "ếch", "lươn", "ốc", "sò", "bạch tuộc", "mực", "tôm hùm", "cua biển", "cá hồi",
        "cá thu", "cá ngừ", "cá trê", "cá lóc", "cá rô", "cá chép", "cá trắm", "cá mè",
        "cá trôi", "cá chạch", "cá bống", "cá bớp", "cá đối", "cá kèo", "cá linh",
        "cá lăng", "cá nheo", "cá quả", "cá trắng", "cá đen", "cá vàng", "cá xanh",
        "cá đỏ", "cá tím", "cá cam", "cá hồng", "cá xám", "cá nâu"
    ]
    
    # Danh sách nguyên liệu phụ
    side_ingredients_keywords = [
        "hành", "tỏi", "gừng", "nghệ", "ớt", "tiêu", "muối", "đường", "nước mắm",
        "dầu", "mỡ", "bơ", "sữa", "kem", "bột", "bột năng", "bột gạo", "nước",
        "rau thơm", "ngò", "húng", "tía tô", "kinh giới", "hành lá", "ngò gai",
        "tôm khô", "cá khô", "mắm", "nước mắm", "dầu ăn", "mỡ heo", "rau răm",
        "rau mùi", "rau húng", "rau tía tô", "rau kinh giới", "rau húng quế",
        "rau húng chó", "rau húng lủi", "rau húng cây", "rau húng chanh"
    ]
    
    main_ingredients = []
    side_ingredients = []
    allergic_ingredients = []
    warnings = []
    
    for ingredient in ingredients:
        ingredient_lower = ingredient.lower()
        
        # Kiểm tra dị ứng
        for allergy in user_allergies:
            if allergy.lower() in ingredient_lower:
                allergic_ingredients.append(ingredient)
                break
        
        # Phân loại nguyên liệu
        is_main = any(keyword in ingredient_lower for keyword in main_ingredients_keywords)
        is_side = any(keyword in ingredient_lower for keyword in side_ingredients_keywords)
        
        if is_main:
            main_ingredients.append(ingredient)
        elif is_side:
            side_ingredients.append(ingredient)
        else:
            # Mặc định là nguyên liệu chính nếu không xác định được
            main_ingredients.append(ingredient)
    
    # Kiểm tra an toàn
    main_allergic = [ing for ing in allergic_ingredients if ing in main_ingredients]
    side_allergic = [ing for ing in allergic_ingredients if ing in side_ingredients]
    
    is_safe = len(main_allergic) == 0
    
    if side_allergic:
        warnings.append(f"Món ăn có chứa nguyên liệu phụ có thể gây dị ứng: {', '.join(side_allergic)}. Bạn có thể cân nhắc loại bỏ nguyên liệu này khi nấu.")
    
    return {
        "is_safe": is_safe,
        "main_ingredients": main_ingredients,
        "side_ingredients": side_ingredients,
        "allergic_ingredients": allergic_ingredients,
        "warnings": warnings,
        "reasoning": f"Món ăn {'an toàn' if is_safe else 'không an toàn'} dựa trên phân tích nguyên liệu"
    } 