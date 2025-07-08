#!/usr/bin/env python3
"""
Test để kiểm tra format dữ liệu trả về đã được tối ưu hóa
"""

import requests
import json

def test_optimized_response():
    """Test API với format dữ liệu mới"""
    
    # Test data
    test_data = {
        "user_id": "507f1f77bcf86cd799439011",  # Thay bằng user_id thực tế
        "question": "Tôi muốn tìm món ăn phù hợp"
    }
    
    # Gọi API
    try:
        response = requests.post(
            "http://localhost:8000/langgraph-workflow",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("=== KẾT QUẢ TỐI ƯU HÓA ===")
            print(f"Status: {result.get('status')}")
            print(f"Message: {result.get('message')}")
            
            # Kiểm tra cấu trúc dữ liệu mới
            if result.get('status') == 'success':
                print(f"\n=== THÔNG TIN USER ===")
                user_info = result.get('user_info', {})
                print(f"Tên: {user_info.get('name')}")
                print(f"Tuổi: {user_info.get('age')}")
                print(f"BMI: {user_info.get('bmi')} ({user_info.get('bmi_category')})")
                print(f"Bệnh lý: {user_info.get('medical_conditions')}")
                
                print(f"\n=== LỰA CHỌN CỦA USER ===")
                print(f"Cảm xúc: {result.get('selected_emotion')}")
                print(f"Phương pháp nấu: {result.get('selected_cooking_methods')}")
                
                print(f"\n=== DANH SÁCH MÓN ĂN ===")
                foods = result.get('foods', [])
                print(f"Tổng số món: {len(foods)}")
                
                # Nhóm theo category
                categories = {}
                for food in foods:
                    category = food.get('category', 'Unknown')
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(food.get('name'))
                
                for category, food_names in categories.items():
                    print(f"\n{category}:")
                    for name in food_names[:5]:  # Chỉ hiển thị 5 món đầu
                        print(f"  - {name}")
                    if len(food_names) > 5:
                        print(f"  ... và {len(food_names) - 5} món khác")
                
                print(f"\n=== THÔNG TIN CHI TIẾT MÓN ĂN ===")
                if foods:
                    sample_food = foods[0]
                    print(f"Mẫu món ăn:")
                    print(f"  - Tên: {sample_food.get('name')}")
                    print(f"  - ID: {sample_food.get('id')}")
                    print(f"  - Mô tả: {sample_food.get('description', 'N/A')}")
                    print(f"  - Phương pháp nấu: {sample_food.get('cook_method', 'N/A')}")
                    print(f"  - Chế độ ăn: {sample_food.get('diet', 'N/A')}")
                    print(f"  - Danh mục: {sample_food.get('category')}")
                
                print(f"\n=== TIMESTAMP ===")
                print(f"Thời gian: {result.get('timestamp')}")
                
                # Kiểm tra kích thước dữ liệu
                data_size = len(json.dumps(result, ensure_ascii=False))
                print(f"\n=== KÍCH THƯỚC DỮ LIỆU ===")
                print(f"Tổng kích thước: {data_size} bytes")
                print(f"Kích thước foods: {len(json.dumps(foods, ensure_ascii=False))} bytes")
                
            elif result.get('status') == 'need_emotion':
                print(f"\n=== CẦN CHỌN CẢM XÚC ===")
                print(f"Session ID: {result.get('session_id')}")
                print(f"Emotion prompt: {result.get('emotion_prompt')}")
                
            elif result.get('status') == 'need_cooking_method':
                print(f"\n=== CẦN CHỌN PHƯƠNG PHÁP NẤU ===")
                print(f"Session ID: {result.get('session_id')}")
                print(f"Cooking method prompt: {result.get('cooking_method_prompt')}")
                
            else:
                print(f"Kết quả khác: {result}")
                
        else:
            print(f"Lỗi HTTP: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Lỗi kết nối: {str(e)}")

def test_continue_with_emotion():
    """Test tiếp tục workflow với cảm xúc"""
    
    # Giả sử có session_id từ bước trước
    session_id = "test_session_123"  # Thay bằng session_id thực tế
    emotion = "Vui vẻ"
    
    try:
        response = requests.post(
            "http://localhost:8000/continue-with-emotion",
            json={
                "session_id": session_id,
                "emotion": emotion
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n=== KẾT QUẢ SAU KHI CHỌN CẢM XÚC ===")
            print(f"Status: {result.get('status')}")
            print(f"Message: {result.get('message')}")
            
            if result.get('status') == 'success':
                foods = result.get('foods', [])
                print(f"Số món ăn: {len(foods)}")
                
        else:
            print(f"Lỗi HTTP: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Lỗi kết nối: {str(e)}")

if __name__ == "__main__":
    print("Testing optimized response format...\n")
    test_optimized_response()
    # test_continue_with_emotion()  # Uncomment nếu muốn test tiếp tục workflow 