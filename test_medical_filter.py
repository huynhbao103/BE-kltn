#!/usr/bin/env python3
"""
Test để kiểm tra logic lọc món ăn theo bệnh lý
"""

import requests
import json

def test_medical_filter():
    """Test API với bệnh lý cụ thể"""
    
    # Test data với bệnh cao huyết áp
    test_data = {
        "user_id": "507f1f77bcf86cd799439011",  # Thay bằng user_id thực tế
        "question": "Tôi muốn tìm món ăn phù hợp cho người cao huyết áp"
    }
    
    print("=== TEST MEDICAL FILTER ===")
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
            print(f"Foods count: {len(foods)}")
            
            if foods:
                print(f"\n=== FOODS BY CATEGORY ===")
                categories = {}
                for food in foods:
                    category = food.get('category', 'Unknown')
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(food.get('name'))
                
                for category, food_names in categories.items():
                    print(f"\n{category}:")
                    for name in food_names:
                        print(f"  - {name}")
                
                # Kiểm tra xem có món ăn nào không phù hợp với bệnh lý không
                print(f"\n=== VALIDATION ===")
                medical_conditions = result.get('user_info', {}).get('medical_conditions', [])
                print(f"User medical conditions: {medical_conditions}")
                
                invalid_foods = []
                for food in foods:
                    category = food.get('category', '')
                    # Kiểm tra xem category có chứa bệnh lý của user không
                    is_valid = any(condition in category for condition in medical_conditions)
                    if not is_valid:
                        invalid_foods.append({
                            'name': food.get('name'),
                            'category': category
                        })
                
                if invalid_foods:
                    print(f"❌ FOUND {len(invalid_foods)} INVALID FOODS:")
                    for food in invalid_foods:
                        print(f"  - {food['name']} (category: {food['category']})")
                else:
                    print("✅ ALL FOODS ARE VALID FOR USER'S MEDICAL CONDITIONS")
                
                # Kiểm tra điểm số
                print(f"\n=== SCORE ANALYSIS ===")
                scored_foods = [f for f in foods if f.get('score') is not None]
                if scored_foods:
                    scores = [f.get('score', 0) for f in scored_foods]
                    print(f"Average score: {sum(scores) / len(scores):.2f}")
                    print(f"Max score: {max(scores)}")
                    print(f"Min score: {min(scores)}")
                    
                    # Hiển thị top 5 món ăn có điểm cao nhất
                    top_foods = sorted(scored_foods, key=lambda x: x.get('score', 0), reverse=True)[:5]
                    print(f"\nTop 5 foods by score:")
                    for i, food in enumerate(top_foods, 1):
                        print(f"{i}. {food.get('name')} (Score: {food.get('score')})")
                else:
                    print("No scored foods found")
                    
            else:
                print("❌ NO FOODS RETURNED!")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection Error: {str(e)}")

def test_continue_workflow_medical():
    """Test workflow với bệnh lý cụ thể"""
    
    # Giả sử có session_id từ bước trước
    session_id = "test_session_123"  # Thay bằng session_id thực tế
    
    print("\n=== TEST CONTINUE WORKFLOW WITH MEDICAL ===")
    
    # Bước 1: Chọn cảm xúc
    try:
        response1 = requests.post(
            "http://localhost:8000/api/langgraph/continue-emotion",
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
                    "http://localhost:8000/api/langgraph/continue-cooking",
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
                        
                        if foods:
                            print(f"\n=== FINAL FOODS VALIDATION ===")
                            medical_conditions = result2.get('user_info', {}).get('medical_conditions', [])
                            print(f"Medical conditions: {medical_conditions}")
                            
                            # Kiểm tra từng món ăn
                            for i, food in enumerate(foods[:5], 1):
                                category = food.get('category', '')
                                is_valid = any(condition in category for condition in medical_conditions)
                                status = "✅" if is_valid else "❌"
                                print(f"{i}. {status} {food.get('name')} (category: {category})")
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

if __name__ == "__main__":
    print("Testing medical filter logic...\n")
    
    # Test lọc theo bệnh lý
    test_medical_filter()
    
    # Test workflow với bệnh lý
    test_continue_workflow_medical() 