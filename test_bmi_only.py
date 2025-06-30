#!/usr/bin/env python3
"""
Test script cho BMI only (không có BMR)
"""

import requests
import json

def test_bmi_only():
    """Test BMI calculation without BMR"""
    
    base_url = "http://localhost:8000"
    user_id = "6853b11bd413516551798e0a"
    
    print("📊 Testing BMI Only (No BMR)")
    print("=" * 50)
    
    # Test 1: API BMI đơn giản
    print(f"\n🧪 Test 1: POST /api/bmi/calculate")
    print("-" * 40)
    
    data = {
        "user_id": user_id
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/bmi/calculate",
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"📊 BMI: {result.get('bmi')}")
            print(f"📊 Category: {result.get('bmi_category')}")
            
            # Kiểm tra không có BMR và calories
            if 'bmr' not in result and 'calorie_need_per_day' not in result:
                print("✅ Không có BMR và calories (đúng như mong đợi)")
            else:
                print("❌ Vẫn có BMR hoặc calories (không đúng)")
            
            user_info = result.get('user_info', {})
            print(f"👤 User: {user_info.get('name')}, {user_info.get('age')} tuổi")
            print(f"📏 Weight: {user_info.get('weight')}kg, Height: {user_info.get('height')}cm")
            print(f"🏥 Medical Conditions: {user_info.get('medical_conditions')}")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 2: GET API
    print(f"\n🧪 Test 2: GET /api/bmi/user/{user_id}")
    print("-" * 40)
    
    try:
        response = requests.get(f"{base_url}/api/bmi/user/{user_id}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"📊 BMI: {result.get('bmi')}")
            print(f"📊 Category: {result.get('bmi_category')}")
            
            # Kiểm tra không có BMR và calories
            if 'bmr' not in result and 'calorie_need_per_day' not in result:
                print("✅ Không có BMR và calories (đúng như mong đợi)")
            else:
                print("❌ Vẫn có BMR hoặc calories (không đúng)")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 3: Complete workflow
    print(f"\n🧪 Test 3: Complete workflow")
    print("-" * 40)
    
    data = {
        "question": "Tôi muốn biết BMI của mình",
        "user_id": user_id
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/complete/process",
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"📝 Message: {result.get('message')}")
            
            # Kiểm tra message không có BMR và calories
            message = result.get('message', '')
            if 'BMR:' not in message and 'Nhu cầu calo:' not in message:
                print("✅ Message không có BMR và calories (đúng như mong đợi)")
            else:
                print("❌ Message vẫn có BMR hoặc calories (không đúng)")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_response_structure():
    """Test cấu trúc response"""
    
    base_url = "http://localhost:8000"
    user_id = "6853b11bd413516551798e0a"
    
    print(f"\n📋 Testing Response Structure")
    print("=" * 50)
    
    data = {
        "user_id": user_id
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/bmi/calculate",
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Response structure:")
            print(f"  - status: {result.get('status')}")
            print(f"  - user_id: {result.get('user_id')}")
            print(f"  - bmi: {result.get('bmi')}")
            print(f"  - bmi_category: {result.get('bmi_category')}")
            
            print(f"\n✅ User info structure:")
            user_info = result.get('user_info', {})
            print(f"  - name: {user_info.get('name')}")
            print(f"  - age: {user_info.get('age')}")
            print(f"  - weight: {user_info.get('weight')}")
            print(f"  - height: {user_info.get('height')}")
            print(f"  - medical_conditions: {user_info.get('medical_conditions')}")
            
            print(f"\n❌ Removed fields (should not exist):")
            print(f"  - bmr: {'❌' if 'bmr' in result else '✅'}")
            print(f"  - calorie_need_per_day: {'❌' if 'calorie_need_per_day' in result else '✅'}")
            
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("🎯 BMI Only Testing")
    print("=" * 60)
    
    # Kiểm tra server có chạy không
    try:
        response = requests.get("http://localhost:8000/docs")
        if response.status_code == 200:
            print("✅ Server đang chạy")
        else:
            print("❌ Server không phản hồi")
            exit(1)
    except:
        print("❌ Không thể kết nối server. Hãy chạy: uvicorn app.main:app --reload")
        exit(1)
    
    test_bmi_only()
    test_response_structure()
    
    print(f"\n\n🎉 BMI Only Test hoàn thành!")
    print("💡 Thay đổi:")
    print("  - Chỉ tính BMI, không tính BMR")
    print("  - Không có calories trong response")
    print("  - Message chỉ hiển thị BMI và thông tin user")
    print("  - Vẫn giữ medical conditions") 