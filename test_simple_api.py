#!/usr/bin/env python3
"""
Test đơn giản để kiểm tra API
"""

import requests
import json

def test_workflow_info():
    """Test endpoint /workflow-info"""
    print("=== Testing /workflow-info ===")
    
    try:
        response = requests.get("http://localhost:8000/api/langgraph/workflow-info")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"Error Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_process_without_auth():
    """Test endpoint /process without auth (should return 401)"""
    print("\n=== Testing /process without auth ===")
    
    data = {
        "question": "Tôi nên ăn gì để giảm cân?"
    }
    
    try:
        response = requests.post("http://localhost:8000/api/langgraph/process", json=data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Correctly returned 401 for missing auth")
            return True
        else:
            print(f"Unexpected response: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_process_with_invalid_auth():
    """Test endpoint /process with invalid auth"""
    print("\n=== Testing /process with invalid auth ===")
    
    headers = {
        "Authorization": "Bearer invalid_token",
        "Content-Type": "application/json"
    }
    
    data = {
        "question": "Tôi nên ăn gì để giảm cân?"
    }
    
    try:
        response = requests.post("http://localhost:8000/api/langgraph/process", headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Correctly returned 401 for invalid auth")
            return True
        else:
            print(f"Unexpected response: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    """Chạy các test"""
    print("Testing API endpoints\n")
    
    # Test workflow info
    test_workflow_info()
    
    # Test without auth
    test_process_without_auth()
    
    # Test with invalid auth
    test_process_with_invalid_auth()
    
    print("\nTest completed!")

if __name__ == "__main__":
    main() 