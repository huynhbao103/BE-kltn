def get_rerank_foods_prompt(data: dict) -> str:
    """
    Tạo prompt cho việc rerank các món ăn theo thứ tự phù hợp nhất
    """
    user_name = data.get("user_name", "Unknown")
    user_age = data.get("user_age", "N/A")
    bmi_category = data.get("bmi_category", "")
    medical_conditions = data.get("medical_conditions", [])
    selected_emotion = data.get("selected_emotion", "")
    selected_cooking_methods = data.get("selected_cooking_methods", [])
    foods = data.get("foods", [])
    
    # Tạo danh sách món ăn
    foods_list = ""
    for i, food in enumerate(foods, 1):
        foods_list += f"{i}. {food['name']}\n"
        foods_list += f"   - Mô tả: {food['description']}\n"
        foods_list += f"   - Cách chế biến: {food['cook_method']}\n"
        foods_list += f"   - Chế độ ăn: {food['diet']}\n"
        foods_list += f"   - Phù hợp BMI: {food['bmi_category']}\n"
        foods_list += f"   - Calories: {food['calories']}, Protein: {food['protein']}g, Fat: {food['fat']}g, Carbs: {food['carbs']}g\n\n"
    
    # Tạo thông tin bệnh
    conditions_text = "không có bệnh đặc biệt"
    if medical_conditions:
        conditions_text = ", ".join(medical_conditions)
    
    # Tạo thông tin cách chế biến
    cooking_text = "không yêu cầu cụ thể"
    if selected_cooking_methods:
        cooking_text = ", ".join(selected_cooking_methods)
    
    prompt = f"""
Bạn là một chuyên gia dinh dưỡng và ẩm thực. Hãy sắp xếp lại danh sách món ăn sau theo thứ tự phù hợp nhất đến ít phù hợp nhất dựa trên thông tin người dùng.

THÔNG TIN NGƯỜI DÙNG:
- Tên: {user_name}
- Tuổi: {user_age}
- Phân loại BMI: {bmi_category}
- Tình trạng bệnh: {conditions_text}
- Cảm xúc hiện tại: {selected_emotion}
- Cách chế biến ưa thích: {cooking_text}

DANH SÁCH MÓN ĂN:
{foods_list}

TIÊU CHÍ SẮP XẾP (theo thứ tự ưu tiên):
1. Phù hợp với BMI và tình trạng sức khỏe
2. Phù hợp với cảm xúc hiện tại
3. Phù hợp với cách chế biến ưa thích
4. Giá trị dinh dưỡng cân bằng
5. Dễ chế biến và phổ biến

YÊU CẦU:
- Sắp xếp lại danh sách món ăn theo thứ tự phù hợp nhất đến ít phù hợp nhất
- Chỉ trả về danh sách số thứ tự và tên món ăn, mỗi món một dòng
- Format: "1. Tên món ăn"
- Không thêm giải thích hay bình luận khác

DANH SÁCH ĐÃ SẮP XẾP:
"""
    
    return prompt


