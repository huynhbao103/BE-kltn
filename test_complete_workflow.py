#!/usr/bin/env python3
"""
Test script cho luồng hoàn chỉnh
"""

import requests
import json
import jwt
from datetime import datetime, timedelta

def create_jwt_token(user_id: str, secret_key: str = "secret_token") -> str:
    """Tạo JWT token"""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")

def test_complete_workflow():
    """Test luồng hoàn chỉnh"""
    
    base_url = "http://localhost:8000"
    user_id = "6853b11bd413516551798e0a"
    
    print("🎯 Testing Complete Workflow")
    print("=" * 60)
    
    # Test 1: Chỉ phân loại topic (không có user_id)
    print("\n🧪 Test 1: Chỉ phân loại topic")
    print("-" * 40)
    
    data = {
        "question": "Tôi muốn biết BMI"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/complete/process",
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"📝 Status: {result.get('status')}")
            print(f"📝 Message: {result.get('message')}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 2: Luồng hoàn chỉnh với user_id trong body
    print(f"\n🧪 Test 2: Luồng hoàn chỉnh với user_id")
    print("-" * 40)
    
    data = {
        "question": "Tôi muốn biết BMI và BMR của mình",
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
            print(f"📝 Status: {result.get('status')}")
            print(f"📝 Message: {result.get('message')}")
            
            if result.get('user_info'):
                user_info = result['user_info']
                print(f"👤 User: {user_info.get('name')}, {user_info.get('age')} tuổi")
                print(f"🏥 Medical Conditions: {user_info.get('medical_conditions')}")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 3: Luồng hoàn chỉnh với JWT token
    print(f"\n🧪 Test 3: Luồng hoàn chỉnh với JWT token")
    print("-" * 40)
    
    token = create_jwt_token(user_id)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "question": "Tôi muốn biết tình trạng sức khỏe của mình"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/complete/process",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"📝 Status: {result.get('status')}")
            print(f"📝 Message: {result.get('message')}")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 4: Câu hỏi không thuộc chủ đề dinh dưỡng
    print(f"\n🧪 Test 4: Câu hỏi không thuộc chủ đề dinh dưỡng")
    print("-" * 40)
    
    data = {
        "question": "Xe máy có bao nhiêu bánh?",
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
            print(f"📝 Status: {result.get('status')}")
            print(f"📝 Message: {result.get('message')}")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 5: Simple classification
    print(f"\n🧪 Test 5: Simple classification")
    print("-" * 40)
    
    data = {
        "question": "Tôi nên ăn gì để giảm cân?"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/complete/simple",
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"📝 Status: {result.get('status')}")
            print(f"📝 Message: {result.get('message')}")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_workflow_info():
    """Test endpoint workflow-info"""
    
    base_url = "http://localhost:8000"
    
    print(f"\n📋 Testing Workflow Info")
    print("=" * 50)
    
    try:
        response = requests.get(f"{base_url}/api/complete/workflow-info")
        
        if response.status_code == 200:
            info = response.json()
            print("✅ Workflow Info:")
            print(f"📝 Name: {info.get('workflow_name')}")
            print(f"📝 Description: {info.get('description')}")
            
            print(f"\n🔗 Endpoints:")
            endpoints = info.get('endpoints', {})
            for endpoint, details in endpoints.items():
                print(f"  - {endpoint}: {details.get('description')}")
                
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("🎯 Complete Workflow Testing")
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
    
    test_complete_workflow()
    test_workflow_info()
    
    print(f"\n\n🎉 Complete Workflow Test hoàn thành!")
    print("💡 Luồng hoàn chỉnh:")
    print("  - /api/complete/process: Luồng chính (3 cách sử dụng)")
    print("  - /api/complete/simple: Chỉ phân loại topic")
    print("  - /api/complete/workflow-info: Thông tin workflow")
    print("\n📝 Cách sử dụng:")
    print("  1. Chỉ question: Phân loại topic")
    print("  2. Question + user_id: Luồng hoàn chỉnh")
    print("  3. Question + JWT token: Luồng hoàn chỉnh") 