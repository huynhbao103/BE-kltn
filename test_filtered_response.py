#!/usr/bin/env python3
"""
Test để kiểm tra kết quả đã được lọc tổng hợp thay vì trả về tất cả món từ mỗi bước
"""

import requests
import json

def test_filtered_response():
    """Test API với kết quả đã được lọc tổng hợp"""
    
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
            
            print("=== KẾT QUẢ ĐÃ ĐƯỢC LỌC TỔNG HỢP ===")
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
                
                print(f"\n=== DANH SÁCH MÓN ĂN ĐÃ LỌC TỔNG HỢP ===")
                foods = result.get('foods', [])
                print(f"Tổng số món: {len(foods)}")
                
                if foods:
                    print(f"\n=== TOP 10 MÓN ĂN PHÙ HỢP NHẤT ===")
                    for i, food in enumerate(foods[:10], 1):
                        score = food.get('score', 'N/A')
                        print(f"{i}. {food.get('name')} (Điểm: {score})")
                        print(f"   - Phương pháp: {food.get('cook_method', 'N/A')}")
                        print(f"   - Chế độ ăn: {food.get('diet', 'N/A')}")
                        print(f"   - Danh mục: {food.get('category', 'N/A')}")
                        print()
                
                # Kiểm tra xem có món ăn nào bị trùng lặp không
                food_names = [food.get('name') for food in foods]
                unique_names = list(set(food_names))
                if len(food_names) != len(unique_names):
                    print(f"⚠️  CÓ MÓN ĂN TRÙNG LẶP: {len(food_names) - len(unique_names)} món")
                else:
                    print("✅ KHÔNG CÓ MÓN ĂN TRÙNG LẶP")
                
                # Kiểm tra kích thước dữ liệu
                data_size = len(json.dumps(result, ensure_ascii=False))
                print(f"\n=== KÍCH THƯỚC DỮ LIỆU ===")
                print(f"Tổng kích thước: {data_size} bytes")
                print(f"Kích thước foods: {len(json.dumps(foods, ensure_ascii=False))} bytes")
                
                # So sánh với kết quả cũ (nếu có)
                if len(foods) <= 20:
                    print("✅ KẾT QUẢ ĐÃ ĐƯỢC LỌC TỐT (≤ 20 món)")
                else:
                    print(f"⚠️  KẾT QUẢ VẪN QUÁ NHIỀU ({len(foods)} món)")
                
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

def test_continue_workflow():
    """Test tiếp tục workflow với cảm xúc và phương pháp nấu"""
    
    # Giả sử có session_id từ bước trước
    session_id = "test_session_123"  # Thay bằng session_id thực tế
    
    # Bước 1: Chọn cảm xúc
    try:
        response1 = requests.post(
            "http://localhost:8000/continue-with-emotion",
            json={
                "session_id": session_id,
                "emotion": "Vui vẻ"
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response1.status_code == 200:
            result1 = response1.json()
            print(f"\n=== SAU KHI CHỌN CẢM XÚC ===")
            print(f"Status: {result1.get('status')}")
            
            if result1.get('status') == 'need_cooking_method':
                # Bước 2: Chọn phương pháp nấu
                response2 = requests.post(
                    "http://localhost:8000/continue-with-cooking-method",
                    json={
                        "session_id": result1.get('session_id'),
                        "cooking_methods": ["Hấp", "Luộc"]
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                if response2.status_code == 200:
                    result2 = response2.json()
                    print(f"\n=== KẾT QUẢ CUỐI CÙNG ===")
                    print(f"Status: {result2.get('status')}")
                    print(f"Message: {result2.get('message')}")
                    
                    if result2.get('status') == 'success':
                        foods = result2.get('foods', [])
                        print(f"Số món ăn cuối cùng: {len(foods)}")
                        
                        if foods:
                            print(f"\n=== TOP 5 MÓN ĂN CUỐI CÙNG ===")
                            for i, food in enumerate(foods[:5], 1):
                                score = food.get('score', 'N/A')
                                print(f"{i}. {food.get('name')} (Điểm: {score})")
                                print(f"   - Phương pháp: {food.get('cook_method', 'N/A')}")
                                print(f"   - Chế độ ăn: {food.get('diet', 'N/A')}")
                                print()
                
        else:
            print(f"Lỗi HTTP: {response1.status_code}")
            print(f"Response: {response1.text}")
            
    except Exception as e:
        print(f"Lỗi kết nối: {str(e)}")

if __name__ == "__main__":
    print("Testing filtered response...\n")
    test_filtered_response()
    # test_continue_workflow()  # Uncomment nếu muốn test workflow hoàn chỉnh 