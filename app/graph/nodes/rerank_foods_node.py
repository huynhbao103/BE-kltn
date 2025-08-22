import os
from dotenv import load_dotenv
from openai import OpenAI
from typing import Dict, Any, List
from app.services.mongo_service import mongo_service
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
def rerank_foods(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node rerank các món ăn sử dụng LLM theo thứ tự phù hợp nhất
    """
    try:
        user_data = state.get("user_data", {})
        bmi_result = state.get("bmi_result", {})
        selected_emotion = state.get("selected_emotion")
        selected_cooking_methods = state.get("selected_cooking_methods", [])
        aggregated_result = state.get("aggregated_result", {})
        user_question = state.get("question", "")
        
        # Lấy danh sách món ăn đã được tổng hợp
        if not aggregated_result or aggregated_result.get("status") != "success":
            return {"rerank_result": {"status": "error", "message": "Không có dữ liệu món ăn để rerank"}}
        
        aggregated_foods = aggregated_result.get("aggregated_foods", [])
        if not aggregated_foods:
            return {"rerank_result": {"status": "error", "message": "Danh sách món ăn trống"}}
        
        print(f"DEBUG: Reranking {len(aggregated_foods)} foods")
        
        # Lấy thông tin người dùng
        user_name = user_data.get("name", "Unknown")
        user_age = user_data.get("age", "N/A")
        bmi_category = bmi_result.get("bmi_category", "") if bmi_result else ""
        medical_conditions = user_data.get("medicalConditions", [])
        user_allergies = user_data.get("allergies", [])
        
        # Lọc bệnh thực sự
        real_conditions = []
        if medical_conditions:
            for condition in medical_conditions:
                condition_lower = condition.lower().strip()
                if condition_lower not in ["không có", "không bệnh", "không có bệnh", "bình thường", "khỏe mạnh"]:
                    real_conditions.append(condition)
        
        # Lọc món ăn theo dị ứng (nếu có)
        if user_allergies:
            # Lấy thông tin chi tiết món ăn từ MongoDB
            dish_ids = [food.get("dish_id") for food in aggregated_foods if food.get("dish_id")]
            dishes_from_mongo = mongo_service.get_dishes_by_ids(dish_ids)
            
            # Tạo mapping từ dish_id đến dish data
            dish_mapping = {dish["_id"]: dish for dish in dishes_from_mongo}
            
            # Lọc món ăn theo dị ứng
            filtered_foods = []
            for food in aggregated_foods:
                dish_id = food.get("dish_id")
                if dish_id and dish_id in dish_mapping:
                    dish_data = dish_mapping[dish_id]
                    dish_ingredients = dish_data.get("ingredients", [])
                    
                    # Kiểm tra xem món ăn có chứa nguyên liệu dị ứng không
                    has_allergic_ingredient = False
                    for allergy in user_allergies:
                        if allergy.lower() in [ing.lower() for ing in dish_ingredients]:
                            has_allergic_ingredient = True
                            break
                    
                    # Chỉ thêm món ăn không chứa nguyên liệu dị ứng
                    if not has_allergic_ingredient:
                        filtered_foods.append(food)
                else:
                    # Nếu không tìm thấy trong MongoDB, giữ lại món ăn (để an toàn)
                    filtered_foods.append(food)
            
            aggregated_foods = filtered_foods
            print(f"DEBUG: Filtered {len(filtered_foods)} foods after allergy check (removed {len([food.get('dish_id') for food in aggregated_foods if food.get('dish_id')]) - len(filtered_foods)} dishes with allergic ingredients)")
        
        # Chuẩn bị dữ liệu cho LLM
        foods_data = []
        for food in aggregated_foods:
            food_info = {
                "id": food.get("dish_id", ""),
                "name": food.get("dish_name", "Unknown"),
                "cook_method": food.get("cook_method", ""),
                "diet": food.get("diet_name", "")
            }
            foods_data.append(food_info)
        
        # Tạo danh sách món ăn cho prompt
        foods_list = ""
        for i, food in enumerate(foods_data, 1):
            foods_list += f"{i}. {food['name']}\n"
            if food.get('cook_method'):
                foods_list += f"   - Cách chế biến: {food['cook_method']}\n"
            if food.get('diet'):
                foods_list += f"   - Chế độ ăn: {food['diet']}\n"
            foods_list += "\n"
        
        # Tạo thông tin bệnh
        conditions_text = "không có bệnh đặc biệt"
        if real_conditions:
            conditions_text = ", ".join(real_conditions)
        
        # Tạo thông tin dị ứng
        allergies_text = "không có dị ứng"
        if user_allergies:
            allergies_text = ", ".join(user_allergies)
        
        # Tạo thông tin cách chế biến
        cooking_text = "không yêu cầu cụ thể"
        if selected_cooking_methods:
            cooking_text = ", ".join(selected_cooking_methods)
        
        # Tạo prompt mới, rõ ràng và ổn định hơn
        previous_food_ids = state.get("previous_food_ids", [])
        previous_foods_text = ""
        if previous_food_ids:
            previous_foods_text = f"\n\n**Lưu ý QUAN TRỌNG:**\n- KHÔNG ĐƯỢC chọn lại bất kỳ món ăn nào có id trong danh sách sau (đây là các món đã được gợi ý trước đó): {previous_food_ids}\n"

        prompt = f"""Bạn là một chuyên gia dinh dưỡng và ẩm thực hàng đầu. Nhiệm vụ của bạn là giúp người dùng chọn món ăn phù hợp nhất từ một danh sách cho trước.

**Thông tin người dùng:**
- Tên: {user_name}
- Câu hỏi: \"{user_question}\"
- Phân loại BMI: {bmi_category}
- Tình trạng bệnh: {conditions_text}
- Dị ứng: {allergies_text}
- Cảm xúc hiện tại: {selected_emotion}
- Cách chế biến ưa thích: {cooking_text}

**Danh sách món ăn cần xử lý:**
{foods_list}
{previous_foods_text}
**Lưu ý QUAN TRỌNG:**- KHÔNG ĐƯỢC chọn lại bất kỳ món ăn nào có id trong danh sách sau (đây là các món đã được gợi ý trước đó): {previous_food_ids}
**YÊU CẦU:**

**Bước 1: Xác định quy tắc lọc món ăn từ câu hỏi của người dùng.**
- **QUAN TRỌNG:** Nếu câu hỏi KHÔNG chứa bất kỳ từ khóa nào về loại món ăn (như \"chay\", \"mặn\", \"tráng miệng\", \"đồ ăn vặt\", v.v.), bạn phải **GIỮ LẠI TOÀN BỘ DANH SÁCH MÓN ĂN** và chuyển thẳng đến Bước 3 để rerank.
- Nếu câu hỏi yêu cầu có liên quan đến **\"món chay\"**:
  - Quy tắc là **CHỈ GIỮ LẠI MÓN CHAY**.
  - Bạn PHẢI loại bỏ TẤT CẢ các món có chứa thịt, cá, hải sản, trứng và các sản phẩm từ động vật.
- Nếu câu hỏi yêu cầu một loại cụ thể khác (ví dụ: \"tráng miệng\", \"món chính\", \"khai vị\", \"soup\", \"salad\",etc...):
  - Quy tắc là **CHỈ GIỮ LẠI CÁC MÓN THUỘC LOẠI ĐÓ**.
  - Bạn cần tự suy luận dựa vào tên món ăn để phân loại.

**Bước 2: Áp dụng quy tắc lọc (NẾU CÓ).**
- Dựa vào quy tắc ở Bước 1, tạo ra một danh sách món ăn đã được lọc.
- Nếu không có quy tắc lọc, danh sách này chính là danh sách món ăn ban đầu.

**Bước 3: Sắp xếp (Rerank) danh sách món ăn đã lọc.**
- Sắp xếp các món ăn trong danh sách đã lọc theo thứ tự phù hợp nhất với người dùng, dựa trên các tiêu chí sau (ưu tiên từ trên xuống dưới):
  1.  **Sự phù hợp với yêu cầu trong câu hỏi** (nếu có yêu cầu đặc biệt khác ngoài loại món ăn).
  2.  **Sức khỏe:** Phù hợp với tình trạng bệnh ({conditions_text}).
  3.  **Sở thích:** Phù hợp với cách chế biến ({cooking_text}).
  4.  Mức độ phổ biến và cân bằng dinh dưỡng.
- **Loại bỏ** những món không thực sự phù hợp với các tiêu chí trên.
- **TUYỆT ĐỐI KHÔNG ĐƯỢC chọn lại bất kỳ món ăn nào có id nằm trong danh sách đã cung cấp ở trên. TRỪ khi câu hỏi yêu cầu chọn lại món đã gợi ý trước đó.
-**Nếu có món ăn phù hợp**: Trả về **CHỈ danh sách TÊN các món ăn** đã được lọc và sắp xếp.
- **Nếu User CHỈ ĐỊNH YÊU CẦU MỘT MÓN CỤ THỂ**: Trả về CHỈ MỘT MÓN ĂN.
- **Nếu KHÔNG có món ăn phù hợp do dị ứng**: Trả về lời giải thích rõ ràng về lý do không thể gợi ý món ăn, bao gồm:
  - Lời xin lỗi
  - Giải thích về dị ứng (không nêu tên món ăn cụ thể nếu có thể gây dị ứng)
  - Lý do tại sao món ăn không phù hợp


**Bước 4: Trả về kết quả.**
- Trả về **CHỈ danh sách TÊN các món ăn** đã được lọc và sắp xếp.
- Nếu User CHỈ ĐỊNH YÊU CẦU MỘT MÓN CỤ THỂ hoặc GẦN GIỐNG MỘT MÓN CỤ THỂ đó., BẠN PHẢI TRẢ VỀ CHỈ MỘT MÓN ĂN.
- Mỗi món ăn trên một dòng. Không thêm số thứ tự, giải thích hay bất kỳ thông tin nào khác.
"""
        
        print(f"DEBUG: Sending rerank request to LLM for {len(foods_data)} foods")
        print(f"DEBUG: User question: {user_question}")
        print(f"DEBUG: Prompt length: {len(prompt)} characters")
        
        # Gọi LLM để rerank
        try:
            # Sử dụng OpenAI client trực tiếp
            if not client:
                print("WARNING: No OpenAI client available, using original order")
                llm_response = ""
            else:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Bạn là một chuyên gia dinh dưỡng và ẩm thực."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000,
                    temperature=0.7
                )
                
                llm_response = response.choices[0].message.content
                print(f"DEBUG: LLM response received: {len(llm_response)} characters")
                print(f"DEBUG: LLM response content: {llm_response}")
            
            # Parse kết quả từ LLM
            ranked_foods = parse_llm_rerank_response(llm_response, aggregated_foods)
            # Lọc lại các món đã gợi ý trước đó
            filtered_ranked_foods = [food for food in ranked_foods if food.get("dish_id") not in previous_food_ids]
            
            print(f"DEBUG: After parsing, ranked_foods count: {len(filtered_ranked_foods)}")
            if filtered_ranked_foods:
                print(f"DEBUG: First few ranked foods: {[f.get('dish_name', 'Unknown') for f in filtered_ranked_foods[:3]]}")
            
            if filtered_ranked_foods:
                print(f"DEBUG: Successfully reranked {len(filtered_ranked_foods)} foods")
                
                result = {
                    "status": "success",
                    "message": f"Đã rerank và lọc {len(filtered_ranked_foods)} món ăn phù hợp",
                    "ranked_foods": filtered_ranked_foods,
                    "total_count": len(filtered_ranked_foods),
                    "rerank_criteria": {
                        "bmi_category": bmi_category,
                        "medical_conditions": real_conditions,
                        "emotion": selected_emotion,
                        "cooking_methods": selected_cooking_methods
                    }
                }
            else:
                print("DEBUG: LLM did not select any foods, checking if it provided explanation")
                
                # Kiểm tra xem LLM có trả về lời giải thích về dị ứng hoặc lý do không
                explanation_keywords = [
                    "xin lỗi", "không thể", "không phù hợp", "dị ứng", "gây dị ứng",
                    "không an toàn", "không có món", "không tìm thấy"
                ]
                
                has_explanation = any(keyword in llm_response.lower() for keyword in explanation_keywords)
                
                if has_explanation and len(llm_response.strip()) > 30:
                    # LLM đã trả về lời giải thích, sử dụng nó
                    print(f"DEBUG: LLM provided explanation: {llm_response[:100]}...")
                    result = {
                        "status": "llm_explanation_provided",
                        "message": "LLM đã cung cấp lời giải thích",
                        "ranked_foods": [],
                        "total_count": 0,
                        "llm_explanation": llm_response.strip(),
                        "rerank_criteria": {
                            "bmi_category": bmi_category,
                            "medical_conditions": real_conditions,
                            "emotion": selected_emotion,
                            "cooking_methods": selected_cooking_methods
                        }
                    }
                else:
                    # LLM không chọn món nào và không có lời giải thích rõ ràng
                    result = {
                        "status": "success",
                        "message": f"Không tìm thấy món ăn phù hợp với yêu cầu của bạn",
                        "ranked_foods": [],
                        "total_count": 0,
                        "rerank_criteria": {
                            "bmi_category": bmi_category,
                            "medical_conditions": real_conditions,
                            "emotion": selected_emotion,
                            "cooking_methods": selected_cooking_methods
                        }
                    }
                
        except Exception as e:
            print(f"DEBUG: LLM error: {e}")
            # Nếu LLM lỗi, trả về thông báo lỗi thay vì sử dụng thứ tự gốc
            result = {
                "status": "error",
                "message": f"Lỗi khi rerank món ăn: {str(e)}",
                "ranked_foods": [],
                "total_count": 0,
                "rerank_criteria": {
                    "bmi_category": bmi_category,
                    "medical_conditions": real_conditions,
                    "emotion": selected_emotion,
                    "cooking_methods": selected_cooking_methods
                }
            }
        
        return {"rerank_result": result}
        
    except Exception as e:
        return {"rerank_result": {"status": "error", "message": f"Lỗi rerank: {str(e)}"}}

def parse_llm_rerank_response(llm_response: str, original_foods: List[Dict]) -> List[Dict]:
    """
    Parse kết quả rerank từ LLM
    """
    try:
        if not llm_response:
            print("DEBUG: No LLM response to parse")
            return []
            
        print(f"DEBUG: Parsing LLM response: {llm_response[:200]}...")
        
        # Tạo mapping từ tên món ăn đến object gốc
        food_mapping = {}
        for food in original_foods:
            food_name = food.get("dish_name", "").lower().strip()
            food_mapping[food_name] = food
        
        print(f"DEBUG: Created mapping for {len(food_mapping)} original foods")
        print(f"DEBUG: Original food names: {list(food_mapping.keys())[:5]}")
        
        # Tìm các tên món ăn trong response của LLM
        ranked_foods = []
        lines = llm_response.split('\n')
        
        print(f"DEBUG: Processing {len(lines)} lines from LLM response")
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            print(f"DEBUG: Processing line {i+1}: '{line}'")
            
            # Tìm số thứ tự và tên món ăn
            # Format có thể là: "1. Tên món ăn" hoặc "1) Tên món ăn" hoặc "1- Tên món ăn"
            import re
            
            # Pattern để tìm số thứ tự và tên món ăn
            patterns = [
                r'^\d+\.\s*(.+)',  # 1. Tên món
                r'^\d+\)\s*(.+)',  # 1) Tên món
                r'^\d+-\s*(.+)',   # 1- Tên món
                r'^\d+\s+(.+)',    # 1 Tên món
                r'^-\s*(.+)',      # - Tên món
                r'^\*\s*(.+)',     # * Tên món
                r'^•\s*(.+)',      # • Tên món
            ]
            
            food_name = None
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    food_name = match.group(1).strip()
                    print(f"DEBUG: Found food name with pattern {pattern}: '{food_name}'")
                    break
            
            # Nếu không tìm thấy với pattern, thử lấy toàn bộ line nếu không có số
            if not food_name and not re.match(r'^\d+', line):
                food_name = line.strip()
                print(f"DEBUG: Using entire line as food name: '{food_name}'")
            
            if food_name:
                # Tìm món ăn trong mapping
                food_name_lower = food_name.lower().strip()
                print(f"DEBUG: Looking for food: '{food_name_lower}'")
                
                found = False
                for original_name, original_food in food_mapping.items():
                    if food_name_lower in original_name or original_name in food_name_lower:
                        if original_food not in ranked_foods:  # Tránh trùng lặp
                            ranked_foods.append(original_food)
                            print(f"DEBUG: Found match: '{food_name_lower}' -> '{original_name}'")
                            found = True
                            break
                
                if not found:
                    print(f"DEBUG: No match found for: '{food_name_lower}'")
        
        # Chỉ trả về những món mà LLM đã chọn, không thêm món gốc
        # Nếu LLM không trả về món nào, trả về danh sách rỗng
        print(f"DEBUG: LLM selected {len(ranked_foods)} foods out of {len(original_foods)} original foods")
        
        if ranked_foods:
            print(f"DEBUG: Selected foods: {[f.get('dish_name', 'Unknown') for f in ranked_foods]}")
        
        print(f"DEBUG: Parsed {len(ranked_foods)} foods from LLM response")
        return ranked_foods
        
    except Exception as e:
        print(f"DEBUG: Error parsing LLM response: {e}")
        import traceback
        traceback.print_exc()
        return [] 