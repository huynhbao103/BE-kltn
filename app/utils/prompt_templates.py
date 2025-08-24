def get_rerank_foods_prompt(data: dict) -> str:
    """
    Tạo prompt cho việc rerank các món ăn theo thứ tự phù hợp nhất, với lọc loại món ăn theo yêu cầu người dùng.
    """
    user_name = data.get("user_name", "Unknown")
    user_age = data.get("user_age", "N/A")
    bmi_category = data.get("bmi_category", "")
    medical_conditions = data.get("medical_conditions", [])
    selected_emotion = data.get("selected_emotion", "")
    selected_cooking_methods = data.get("selected_cooking_methods", [])
    foods = data.get("foods", [])
    user_question = data.get("user_question", "")  # Thêm câu hỏi của người dùng
    food_type_preference = data.get("food_type_preference", "")  # Thêm loại món ưa thích

    # Tạo danh sách món ăn
    foods_list = ""
    for i, food in enumerate(foods, 1):
        foods_list += f"{i}. {food['name']}\n"
        if food.get('cook_method'):
            foods_list += f"   - Cách chế biến: {food['cook_method']}\n"
        if food.get('diet'):
            foods_list += f"   - Chế độ ăn: {food['diet']}\n"
        foods_list += "\n"

    # Tạo thông tin bệnh
    conditions_text = "không có bệnh đặc biệt"
    if medical_conditions:
        conditions_text = ", ".join(medical_conditions)

    # Tạo thông tin cách chế biến
    cooking_text = "không yêu cầu cụ thể"
    if selected_cooking_methods:
        cooking_text = ", ".join(selected_cooking_methods)

    # Các loại món ăn có thể phân loại
    food_types = """
- chay: món không chứa thịt, cá, hải sản, trứng
- mặn: món có thịt, cá, hải sản
- tráng miệng: bánh, kem, chè, hoa quả
- món chính: cơm, phở, bún, mì, các món ăn chính
- khai vị: gỏi, salad, món ăn nhẹ
- đồ uống: nước ép, sinh tố, trà, cà phê
- bánh: bánh ngọt, bánh mặn, bánh tráng
- soup: canh, súp, cháo
- salad: gỏi, salad rau củ
"""

    prompt = f"""
Bạn là một chuyên gia dinh dưỡng và ẩm thực. Dựa trên câu hỏi của người dùng và thông tin cung cấp, hãy phân loại và rerank danh sách món ăn. Chỉ sử dụng dữ liệu được cung cấp, không thêm dữ liệu bên ngoài.

Câu hỏi của người dùng: {user_question}

QUAN TRỌNG: Nếu người dùng yêu cầu món chay, bạn PHẢI loại bỏ TẤT CẢ các món có chứa:
- Thịt (thịt bò, thịt heo, thịt gà, thịt vịt, thịt dê, thịt cừu...)
- Cá, hải sản (tôm, cua, mực, ốc, sò, bạch tuộc, lươn...)
- Trứng (trứng gà, trứng vịt...)
- Bất kỳ động vật nào

Chỉ giữ lại món ăn thuần chay (rau, củ, quả, đậu, nấm, ngũ cốc...).

THÔNG TIN NGƯỜI DÙNG:
- Tên: {user_name}
- Tuổi: {user_age}
- Phân loại BMI: {bmi_category}
- Tình trạng bệnh: {conditions_text}
- Cảm xúc hiện tại: {selected_emotion}
- Cách chế biến ưa thích: {cooking_text}
- Loại món ưa thích: {food_type_preference}

Các loại món ăn có thể phân loại:
{food_types}

DANH SÁCH MÓN ĂN:
{foods_list}

Lưu ý:
- Không hiển thị các món ăn không phù hợp với yêu cầu của người dùng.
- Không hiển thị các món ăn không phù hợp với cảm xúc của người dùng.
- Không hiển thị các món ăn không phù hợp với cách chế biến của người dùng.
- Không hiển thị các món ăn không phù hợp với loại món ưa thích của người dùng.

YÊU CẦU:
1. Lọc danh sách món ăn:
   - Nếu câu hỏi của người dùng chứa từ khóa liên quan đến loại món ăn (ví dụ: "chay", "mặn", "tráng miệng", "món chính", "khai vị", "đồ uống", "bánh", "soup", "salad", "chè"), chỉ giữ lại tên món ăn phù hợp với nó.
   - Nếu từ khóa là "chay", kiểm tra kỹ trường tên món ăn có chứa từ "thịt", "cá", "hải sản", "trứng" hay không để loại bỏ bất kỳ món nào chứa thịt, cá, hải sản, hoặc trứng.
   - Nếu không có từ khóa loại món ăn trong câu hỏi, ưu tiên loại món ưa thích ({food_type_preference}).
   - Loại bỏ tất cả các món không thuộc loại được xác định.

2. Rerank danh sách món ăn đã lọc theo thứ tự ưu tiên, nếu món không phù hợp với yêu cầu của người dùng thì loại bỏ:
   - Phù hợp với BMI ({bmi_category})
   - Tốt cho tình trạng sức khỏe ({conditions_text})
   - Phù hợp với cảm xúc ({selected_emotion})
   - Phù hợp với cách chế biến ({cooking_text})
   - Giá trị dinh dưỡng cân bằng (ưu tiên protein, giảm fat và carbs nếu BMI cao)
   - Dễ chế biến và phổ biến

3. Kiểm tra lại lần cuối để đảm bảo không có món mặn nào trong danh sách nếu loại món được yêu cầu là "chay".

4. Trả về danh sách món ăn phù hợp nhất theo định dạng:
- Tên món 1
- Tên món 2
- Tên món 3
...

Chỉ trả về danh sách tên món ăn, không giải thích hay thêm thông tin bổ sung.
"""
    
    return prompt

def get_natural_response_prompt(question: str, user_info: dict, food_info: list, cooking_methods: list, weather: str, time_of_day: str, topic_classification: str, constraints_info: dict = None) -> str:
    """
    Tạo prompt cho việc tạo câu trả lời tự nhiên bằng LLM
    """
    user_name = user_info.get("name", "Unknown")
    user_age = user_info.get("age", "N/A")
    bmi_category = user_info.get("bmi_category", "N/A")
    medical_conditions = user_info.get("medical_conditions", [])
    allergies = user_info.get("allergies", [])
    
    # Xử lý thông tin constraints nếu có (không hiển thị excluded methods)
    constraints_text = ""
    if constraints_info:
        if constraints_info.get("aggregated_message"):
            constraints_text += f"ℹ️ Thông tin tìm kiếm: {constraints_info['aggregated_message']}\n"
        
        # Thêm thông tin cảnh báo dị ứng nếu có
        if constraints_info.get("allergy_warnings"):
            constraints_text += "\n⚠️ CẢNH BÁO DỊ ỨNG:\n"
            allergy_warnings = constraints_info.get("allergy_warnings", {})
            for source_key, warnings in allergy_warnings.items():
                for warning in warnings:
                    dish_name = warning.get("dish_name", "Unknown")
                    warning_text = warning.get("warnings", [])
                    if warning_text:
                        constraints_text += f"• {dish_name}: {', '.join(warning_text)}\n"
    
    # Tạo thông tin món ăn
    foods_text = ""
    if food_info:
        for i, food in enumerate(food_info[:10], 1):  # Chỉ lấy 5 món đầu để tránh prompt quá dài
            foods_text += f"{i}. {food['name']}"
            if food.get('description'):
                foods_text += f" - {food['description']}"
            if food.get('cook_method'):
                foods_text += f" (Chế biến: {food['cook_method']})"
            foods_text += "\n"
    else:
        foods_text = "Không tìm thấy món ăn phù hợp với các tiêu chí hiện tại."
    
    # Tạo thông tin bệnh
    conditions_text = "không có bệnh đặc biệt"
    if medical_conditions and medical_conditions != ["Không có"]:
        conditions_text = ", ".join(medical_conditions)
    
    # Tạo thông tin dị ứng
    allergies_text = "không có dị ứng"
    if allergies and allergies != ["Không có"]:
        allergies_text = ", ".join(allergies)
    
    # Tạo thông tin cách chế biến
    cooking_text = "không yêu cầu cụ thể"
    if cooking_methods:
        cooking_text = ", ".join(cooking_methods)
    
    # Tạo thông tin thời tiết và thời gian
    context_text = ""
    if weather and time_of_day:
        context_text = f"Thời tiết hiện tại: {weather}, Thời gian: {time_of_day}"
    
    # Xác định xem có món ăn hay không để điều chỉnh prompt
    has_foods = bool(food_info)
    
    # Thêm hướng dẫn về xử lý dị ứng
    allergy_instruction = ""
    if allergies and allergies != ["Không có"]:
        allergy_instruction = f"""
LƯU Ý QUAN TRỌNG VỀ DỊ ỨNG:
- Người dùng bị dị ứng với: {allergies_text}
- Nếu có món ăn chứa nguyên liệu gây dị ứng, hãy nhắc nhở rõ ràng
- Khuyến khích người dùng cẩn thận khi chế biến và ăn uống
- Đề xuất cách thay thế hoặc điều chỉnh món ăn để tránh dị ứng
"""
    
    prompt = f"""
Bạn là một chuyên gia dinh dưỡng thân thiện và am hiểu về lĩnh vực ẩm thực của Việt Nam. Hãy tạo một câu trả lời tự nhiên, thân thiện và hữu ích cho người dùng dựa trên thông tin sau:

CÂU HỎI CỦA NGƯỜI DÙNG: {question}

THÔNG TIN NGƯỜI DÙNG:
- Tên: {user_name}
- Tuổi: {user_age}
- Phân loại BMI: {bmi_category}
- Tình trạng bệnh: {conditions_text}
- Dị ứng: {allergies_text}
- Cách chế biến ưa thích: {cooking_text}
- {context_text}

{constraints_text}

CÁC MÓN ĂN PHÙ HỢP:
{foods_text}

{allergy_instruction}

YÊU CẦU:
1. Tạo câu trả lời tự nhiên, thân thiện như đang trò chuyện với bạn bè
2. {'Giải thích ngắn gọn tại sao những món này phù hợp với người dùng' if has_foods else 'Giải thích ngắn gọn tại sao không tìm thấy món ăn phù hợp và đưa ra lời khuyên'}
3. Đề cập đến các yếu tố như BMI, bệnh lý, dị ứng nếu có
4. Nếu có thông tin thời tiết/thời gian, hãy đề cập đến sự phù hợp
5. {'Khuyến khích người dùng thử các món ăn được gợi ý' if has_foods else 'Đưa ra lời khuyên thay thế hoặc gợi ý điều chỉnh tiêu chí tìm kiếm'}
6. Độ dài câu trả lời khoảng 2-4 câu, không quá dài
7. Sử dụng ngôn ngữ tự nhiên, không cứng nhắc như bot
8. LƯU Ý ĐẶC BIỆT: CHỈ LẤY CÁC MÓN ĂN PHÙ HỢP TỪ DỮ LIỆU CỦA TÔI , KHÔNG THÊM MÓN ĂN BÊN NGOÀI NÀO KHÁC
9. {'Liệt kê lại tên các món ăn trong câu trả lời, đề cập đến chúng một cách tự nhiên' if has_foods else 'Không đề xuất món ăn nào ngoài dữ liệu'}
10. Lưu ý: không được thêm bất kỳ món ăn nào bên ngoài dữ liệu của tôi
11. Nếu có thông tin gì khác thì cũng nói rõ ràng cho người dùng
12. Trả lời cục súc, có thể chửi thề, không quá dài, không quá ngắn
13. {'Nếu không có món ăn phù hợp, hãy khuyên người dùng thử thay đổi tiêu chí hoặc đưa ra lời khuyên chung về dinh dưỡng' if not has_foods else ''}
14. QUAN TRỌNG: Nếu có cảnh báo dị ứng, hãy nhắc nhở người dùng cẩn thận và đưa ra lời khuyên cụ thể về cách tránh dị ứng
15. Nếu món ăn có chứa nguyên liệu gây dị ứng, hãy đề xuất cách thay thế hoặc điều chỉnh để an toàn
"""
    
    return prompt