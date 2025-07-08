#!/usr/bin/env python3
"""
Test với JWT token hợp lệ
"""

import requests
import json
import jwt
from datetime import datetime, timedelta, timezone

# JWT Secret key (phải giống với config.py)
JWT_SECRET_KEY = "your-secret-key-change-in-production"

def create_test_jwt(user_id: str) -> str:
    """Tạo JWT token cho test"""
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

def test_process_with_valid_jwt():
    """Test endpoint /process với JWT hợp lệ"""
    print("=== Testing /process with valid JWT ===")
    
    # Tạo JWT token cho user test
    user_id = "507f1f77bcf86cd799439011"  # ObjectId hợp lệ
    token = create_test_jwt(user_id)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "question": "Tôi nên ăn gì để giảm cân?"
    }
    
    try:
        response = requests.post("http://localhost:8000/api/langgraph/process", headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
        else:
            print(f"Error Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def test_emotion_with_valid_jwt(session_id: str):
    """Test endpoint /process-emotion với JWT hợp lệ"""
    print(f"\n=== Testing /process-emotion with session: {session_id} ===")
    
    user_id = "507f1f77bcf86cd799439011"
    token = create_test_jwt(user_id)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "session_id": session_id,
        "emotion": "Vui vẻ"
    }
    
    try:
        response = requests.post("http://localhost:8000/api/langgraph/process-emotion", headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
        else:
            print(f"Error Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def test_cooking_method_with_valid_jwt(session_id: str):
    """Test endpoint /process-cooking-method với JWT hợp lệ"""
    print(f"\n=== Testing /process-cooking-method with session: {session_id} ===")
    
    user_id = "507f1f77bcf86cd799439011"
    token = create_test_jwt(user_id)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "session_id": session_id,
        "cooking_methods": ["Luộc", "Hấp"]
    }
    
    try:
        response = requests.post("http://localhost:8000/api/langgraph/process-cooking-method", headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
        else:
            print(f"Error Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def main():
    """Chạy test với JWT hợp lệ"""
    print("Testing API with valid JWT\n")
    
    # Test process endpoint
    result1 = test_process_with_valid_jwt()
    
    if result1 and result1.get("status") == "need_emotion":
        session_id = result1.get("session_id")
        
        # Test emotion endpoint
        result2 = test_emotion_with_valid_jwt(session_id)
        
        if result2 and result2.get("status") == "need_cooking_method":
            session_id2 = result2.get("session_id")
            
            # Test cooking method endpoint
            test_cooking_method_with_valid_jwt(session_id2)
    
    print("\nTest completed!")

if __name__ == "__main__":
    main() 