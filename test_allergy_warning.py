#!/usr/bin/env python3
"""
Test script để kiểm tra logic cảnh báo dị ứng
"""

def test_allergy_warning_generation():
    """Test việc tạo cảnh báo dị ứng"""
    
    # Mock data từ filtered_result
    filtered_result = {
        "allergy_warnings": {
            "source_1": [
                {
                    "dish_name": "Canh Chua Cá",
                    "warnings": ["Món ăn có chứa nguyên liệu phụ có thể gây dị ứng: cá. Bạn có thể cân nhắc loại bỏ nguyên liệu này khi nấu."]
                }
            ],
            "source_2": [
                {
                    "dish_name": "Tôm Rang Muối",
                    "warnings": ["Món ăn có chứa nguyên liệu phụ có thể gây dị ứng: tôm. Bạn có thể cân nhắc loại bỏ nguyên liệu này khi nấu."]
                }
            ]
        },
        "removed_foods": {
            "source_1": [
                {
                    "dish_name": "Cá Hấp",
                    "reason": "Chứa nguyên liệu gây dị ứng: cá",
                    "allergic_ingredients": ["cá"]
                }
            ]
        }
    }
    
    # Test tạo cảnh báo dị ứng
    allergy_warnings = filtered_result.get("allergy_warnings", {})
    print(f"Allergy warnings found: {allergy_warnings}")
    
    # Tạo thông tin cảnh báo dị ứng
    allergy_alert = ""
    if allergy_warnings:
        allergy_alert = "\n⚠️ CẢNH BÁO DỊ ỨNG:\n"
        for source_key, warnings in allergy_warnings.items():
            for warning in warnings:
                dish_name = warning.get("dish_name", "Unknown")
                warning_text = warning.get("warnings", [])
                if warning_text:
                    allergy_alert += f"• {dish_name}: {', '.join(warning_text)}\n"
    
    print(f"Generated allergy alert:\n{allergy_alert}")
    
    # Test với user có dị ứng
    user_allergies = ["cá", "tôm"]
    print(f"User allergies: {user_allergies}")
    
    # Kiểm tra xem có món ăn nào bị loại bỏ không
    removed_foods = filtered_result.get("removed_foods", {})
    if removed_foods:
        print("\nMón ăn bị loại bỏ do dị ứng:")
        for source_key, foods in removed_foods.items():
            for food in foods:
                print(f"• {food['dish_name']}: {food['reason']}")
    
    return allergy_alert

def test_prompt_generation():
    """Test việc tạo prompt với thông tin dị ứng"""
    
    user_info = {
        "name": "Test User",
        "age": 25,
        "bmi_category": "Bình thường",
        "medical_conditions": ["Không có"],
        "allergies": ["cá", "tôm"]
    }
    
    constraints_info = {
        "allergy_warnings": {
            "source_1": [
                {
                    "dish_name": "Canh Chua Cá",
                    "warnings": ["Món ăn có chứa nguyên liệu phụ có thể gây dị ứng: cá"]
                }
            ]
        }
    }
    
    # Tạo thông tin cảnh báo dị ứng
    constraints_text = ""
    if constraints_info.get("allergy_warnings"):
        constraints_text += "\n⚠️ CẢNH BÁO DỊ ỨNG:\n"
        allergy_warnings = constraints_info.get("allergy_warnings", {})
        for source_key, warnings in allergy_warnings.items():
            for warning in warnings:
                dish_name = warning.get("dish_name", "Unknown")
                warning_text = warning.get("warnings", [])
                if warning_text:
                    constraints_text += f"• {dish_name}: {', '.join(warning_text)}\n"
    
    # Tạo hướng dẫn về xử lý dị ứng
    allergies_text = ", ".join(user_info.get("allergies", []))
    allergy_instruction = f"""
LƯU Ý QUAN TRỌNG VỀ DỊ ỨNG:
- Người dùng bị dị ứng với: {allergies_text}
- Nếu có món ăn chứa nguyên liệu gây dị ứng, hãy nhắc nhở rõ ràng
- Khuyến khích người dùng cẩn thận khi chế biến và ăn uống
- Đề xuất cách thay thế hoặc điều chỉnh món ăn để tránh dị ứng
"""
    
    print("Constraints text:")
    print(constraints_text)
    print("\nAllergy instruction:")
    print(allergy_instruction)

if __name__ == "__main__":
    print("=== Testing Allergy Warning Generation ===")
    test_allergy_warning_generation()
    
    print("\n=== Testing Prompt Generation ===")
    test_prompt_generation()
    
    print("\n✅ All tests completed!")
