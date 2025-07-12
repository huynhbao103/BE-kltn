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