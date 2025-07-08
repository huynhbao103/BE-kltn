#!/usr/bin/env python3
"""
Test script để kiểm tra API endpoints
"""

import requests
import json

# Base URL của API
BASE_URL = "http://localhost:8000/api/langgraph"

# JWT Token (thay thế bằng token thật)
JWT_TOKEN = "your_jwt_token_here"

def test_workflow_info():
    """Test endpoint /workflow-info"""
    print("=== Testing /workflow-info ===")
    
    try:
        response = requests.get(f"{BASE_URL}/workflow-info")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_process_endpoint():
    """Test endpoint /process"""
    print("\n=== Testing /process ===")
    
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "question": "Tôi nên ăn gì để giảm cân?"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/process", headers=headers, json=data)
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

def test_emotion_endpoint(session_id, emotion):
    """Test endpoint /process-emotion"""
    print(f"\n=== Testing /process-emotion with emotion: {emotion} ===")
    
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "session_id": session_id,
        "emotion": emotion
    }
    
    try:
        response = requests.post(f"{BASE_URL}/process-emotion", headers=headers, json=data)
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

def test_cooking_method_endpoint(session_id, cooking_methods):
    """Test endpoint /process-cooking-method"""
    print(f"\n=== Testing /process-cooking-method with methods: {cooking_methods} ===")
    
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "session_id": session_id,
        "cooking_methods": cooking_methods
    }
    
    try:
        response = requests.post(f"{BASE_URL}/process-cooking-method", headers=headers, json=data)
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
    """Chạy tất cả các test"""
    print("Testing API endpoints\n")
    
    # Test workflow info
    test_workflow_info()
    
    # Test process endpoint
    result1 = test_process_endpoint()
    
    if result1 and result1.get("status") == "need_emotion":
        session_id = result1.get("session_id")
        
        # Test emotion endpoint
        result2 = test_emotion_endpoint(session_id, "Vui vẻ")
        
        if result2 and result2.get("status") == "need_cooking_method":
            session_id2 = result2.get("session_id")
            
            # Test cooking method endpoint
            test_cooking_method_endpoint(session_id2, ["Luộc", "Hấp"])
    
    print("\nTest completed!")

if __name__ == "__main__":
    main() 