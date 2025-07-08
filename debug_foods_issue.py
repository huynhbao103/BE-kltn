#!/usr/bin/env python3
"""
Debug script để kiểm tra tại sao foods không hiển thị trong kết quả
"""

import requests
import json

def debug_foods_issue():
    """Debug vấn đề foods không hiển thị"""
    
    # Test data với cảm xúc "Buồn bã"
    test_data = {
        "user_id": "507f1f77bcf86cd799439011",  # Thay bằng user_id thực tế
        "question": "Tôi muốn tìm món ăn phù hợp"
    }
    
    print("=== DEBUG FOODS ISSUE ===")
    print(f"Test data: {test_data}")
    
    # Gọi API
    try:
        response = requests.post(
            "http://localhost:8000/api/langgraph/process",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n=== RESPONSE STATUS ===")
            print(f"Status: {result.get('status')}")
            print(f"Message: {result.get('message')}")
            
            # Kiểm tra foods
            foods = result.get('foods', [])
            print(f"\n=== FOODS ANALYSIS ===")
            print(f"Foods type: {type(foods)}")
            print(f"Foods length: {len(foods)}")
            print(f"Foods content: {foods}")
            
            if foods:
                print(f"\n=== FIRST 3 FOODS ===")
                for i, food in enumerate(foods[:3], 1):
                    print(f"{i}. {food}")
            else:
                print("❌ FOODS IS EMPTY!")
                
                # Kiểm tra các trường khác
                print(f"\n=== OTHER FIELDS ===")
                print(f"User info: {result.get('user_info')}")
                print(f"Selected emotion: {result.get('selected_emotion')}")
                print(f"Selected cooking methods: {result.get('selected_cooking_methods')}")
                
                # Kiểm tra message để xem có thông tin gì về foods không
                message = result.get('message', '')
                if 'Đã tìm thấy' in message:
                    print(f"✅ Message indicates foods were found")
                else:
                    print(f"❌ Message doesn't mention foods")
                    
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection Error: {str(e)}")

def test_continue_workflow_debug():
    """Test workflow với cảm xúc Buồn bã"""
    
    # Giả sử có session_id từ bước trước
    session_id = "test_session_123"  # Thay bằng session_id thực tế
    
    print("\n=== TEST CONTINUE WORKFLOW ===")
    
    # Bước 1: Chọn cảm xúc "Buồn bã"
    try:
        response1 = requests.post(
            "http://localhost:8000/continue-with-emotion",
            json={
                "session_id": session_id,
                "emotion": "Buồn bã"
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response1.status_code == 200:
            result1 = response1.json()
            print(f"Step 1 - Status: {result1.get('status')}")
            
            if result1.get('status') == 'need_cooking_method':
                # Bước 2: Chọn phương pháp nấu
                response2 = requests.post(
                    "http://localhost:8000/continue-with-cooking-method",
                    json={
                        "session_id": result1.get('session_id'),
                        "cooking_methods": ["Luộc", "Hấp"]
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                if response2.status_code == 200:
                    result2 = response2.json()
                    print(f"Step 2 - Status: {result2.get('status')}")
                    print(f"Step 2 - Message: {result2.get('message')}")
                    
                    if result2.get('status') == 'success':
                        foods = result2.get('foods', [])
                        print(f"Step 2 - Foods count: {len(foods)}")
                        print(f"Step 2 - Foods: {foods[:3] if foods else 'Empty'}")
                    else:
                        print(f"Step 2 - Error: {result2}")
                else:
                    print(f"Step 2 - HTTP Error: {response2.status_code}")
            else:
                print(f"Step 1 - Unexpected status: {result1}")
        else:
            print(f"Step 1 - HTTP Error: {response1.status_code}")
            
    except Exception as e:
        print(f"❌ Workflow Error: {str(e)}")

def check_api_endpoints():
    """Kiểm tra các API endpoints có hoạt động không"""
    
    print("\n=== CHECK API ENDPOINTS ===")
    
    endpoints = [
        "http://localhost:8000/langgraph-workflow",
        "http://localhost:8000/continue-with-emotion", 
        "http://localhost:8000/continue-with-cooking-method"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint.replace("/langgraph-workflow", "/docs"))
            if response.status_code == 200:
                print(f"✅ {endpoint} - Available")
            else:
                print(f"❌ {endpoint} - Not available ({response.status_code})")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {str(e)}")

if __name__ == "__main__":
    print("Debugging foods display issue...\n")
    
    # Kiểm tra API endpoints
    check_api_endpoints()
    
    # Debug vấn đề foods
    debug_foods_issue()
    
    # Test workflow
    test_continue_workflow_debug() 