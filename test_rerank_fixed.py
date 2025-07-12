#!/usr/bin/env python3
"""
Test workflow với dữ liệu đã sửa
"""

import requests
import json

def test_workflow():
    url = "http://localhost:8000/api/langgraph/process"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNjg3MDQ2Y2IwOGIyMjVlZjA4MGVmNzY3IiwiZXhwIjoxNzUyMzQzNTYxLCJpYXQiOjE3NTIyNTcxNjF9.6qCePM60pDUgpGwU_UvON-KV4N22hT7hYDNFQpfnwXg"
    }
    data = {
        "question": "Tôi muốn ăn chay"
    }
    
    print("=== Testing Workflow with Fixed Data ===")
    print(f"URL: {url}")
    print(f"Question: {data['question']}")
    print("-" * 50)
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                json_response = response.json()
                print(f"Response: {json.dumps(json_response, indent=2, ensure_ascii=False)}")
                
                # Nếu cần chọn cảm xúc, tiếp tục workflow
                if json_response.get("status") == "need_emotion":
                    session_id = json_response.get("session_id")
                    print(f"\n=== Continuing with emotion selection ===")
                    print(f"Session ID: {session_id}")
                    
                    # Chọn cảm xúc và phương pháp nấu
                    continue_url = "http://localhost:8000/api/langgraph/process-emotion-cooking"
                    continue_data = {
                        "session_id": session_id,
                        "emotion": "Vui vẻ",
                        "cooking_methods": ["Luộc", "Xào"]
                    }
                    
                    continue_response = requests.post(continue_url, headers=headers, json=continue_data)
                    print(f"Continue Status Code: {continue_response.status_code}")
                    
                    if continue_response.status_code == 200:
                        continue_json = continue_response.json()
                        print(f"Final Response: {json.dumps(continue_json, indent=2, ensure_ascii=False)}")
                    else:
                        print(f"Continue Error: {continue_response.text}")
                        
            except:
                print(f"Response: {response.text}")
        else:
            print(f"Error Response: {response.text}")
                
    except Exception as e:
        print(f"Exception: {str(e)}")

if __name__ == "__main__":
    test_workflow() 