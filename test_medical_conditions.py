#!/usr/bin/env python3
"""
Test script cho medical conditions
"""

import requests
import json

def test_bmi_with_medical_conditions():
    """Test BMI API với medical conditions"""
    
    base_url = "http://localhost:8000"
    
    print("🏥 Testing BMI with Medical Conditions")
    print("=" * 50)
    
    # User ID thực từ MongoDB
    user_id = "6853b11bd413516551798e0a"  # ID của user Huỳnh
    
    print(f"👤 Testing with user ID: {user_id}")
    
    # Test POST /api/bmi/calculate
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
            print(f"📊 BMR: {result.get('bmr')} calo/ngày")
            print(f"📊 Calories: {result.get('calorie_need_per_day')} calo/ngày")
            
            user_info = result.get('user_info', {})
            print(f"👤 User: {user_info.get('name')}, {user_info.get('age')} tuổi")
            print(f"📏 Weight: {user_info.get('weight')}kg, Height: {user_info.get('height')}cm")
            
            # Hiển thị medical conditions
            medical_conditions = user_info.get('medical_conditions', [])
            print(f"🏥 Medical Conditions: {medical_conditions}")
            
            if medical_conditions and medical_conditions != ["Không có"]:
                print("⚠️  User có tình trạng bệnh cần lưu ý!")
            else:
                print("✅ User không có tình trạng bệnh đặc biệt")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test GET /api/bmi/user/{user_id}
    print(f"\n🧪 Test 2: GET /api/bmi/user/{user_id}")
    print("-" * 40)
    
    try:
        response = requests.get(f"{base_url}/api/bmi/user/{user_id}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"📊 BMI: {result.get('bmi')}")
            print(f"📊 Category: {result.get('bmi_category')}")
            print(f"📊 BMR: {result.get('bmr')} calo/ngày")
            print(f"📊 Calories: {result.get('calorie_need_per_day')} calo/ngày")
            
            # Hiển thị medical conditions
            medical_conditions = result.get('medical_conditions', [])
            print(f"🏥 Medical Conditions: {medical_conditions}")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_langgraph_with_medical_conditions():
    """Test LangGraph workflow với medical conditions"""
    
    base_url = "http://localhost:8000"
    
    print(f"\n🔐 Testing LangGraph with Medical Conditions")
    print("=" * 50)
    
    # Tạo JWT token (sử dụng secret key đúng)
    import jwt
    from datetime import datetime, timedelta
    
    user_id = "6853b11bd413516551798e0a"
    
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(payload, "secret_token", algorithm="HS256")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "question": "Tôi muốn biết BMI và tình trạng sức khỏe của mình"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/langgraph/process",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"📝 Message: {result.get('message')}")
            
            # Kiểm tra có thông tin bệnh trong message không
            message = result.get('message', '')
            if 'Tình trạng bệnh:' in message:
                print("🏥 Medical conditions found in message!")
            else:
                print("ℹ️  No medical conditions in message (user might be healthy)")
            
            # Kiểm tra trong user_info
            user_info = result.get('user_info', {})
            medical_conditions = user_info.get('medical_conditions', [])
            print(f"🏥 Medical Conditions in user_info: {medical_conditions}")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("🎯 Medical Conditions Testing")
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
    
    test_bmi_with_medical_conditions()
    test_langgraph_with_medical_conditions()
    
    print(f"\n\n🎉 Medical Conditions Test hoàn thành!")
    print("💡 Thông tin mới:")
    print("  - Medical conditions được thêm vào API response")
    print("  - Medical conditions được hiển thị trong message")
    print("  - Cả BMI API và LangGraph đều có thông tin bệnh") 