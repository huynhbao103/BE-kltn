#!/usr/bin/env python3
"""
Test debug trực tiếp không cần API
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.graph.engine import run_langgraph_workflow_until_selection
from app.services.mongo_service import mongo_service

def test_direct_debug():
    """Test debug trực tiếp"""
    
    print("=== DIRECT DEBUG TEST ===")
    
    # Test user_id thực tế - user có "Cao huyết áp"
    user_id = "6853b11bd413516551798e0a"
    question = "Tôi muốn tìm món ăn phù hợp"
    
    print(f"Testing with user_id: {user_id}")
    print(f"Question: {question}")
    
    try:
        # Kiểm tra user data trước
        user_data = mongo_service.get_user_health_data(user_id)
        print(f"\n=== USER DATA ===")
        print(f"User data: {user_data}")
        
        if user_data:
            medical_conditions = user_data.get("medicalConditions", [])
            print(f"Medical conditions: {medical_conditions}")
        else:
            print("❌ User not found!")
            return
        
        # Chạy workflow
        print(f"\n=== RUNNING WORKFLOW ===")
        result = run_langgraph_workflow_until_selection(user_id, question)
        
        print(f"\n=== WORKFLOW RESULT ===")
        print(f"Status: {result.get('status')}")
        print(f"Message: {result.get('message')}")
        
        # Kiểm tra foods
        foods = result.get('foods', [])
        print(f"\n=== FOODS CHECK ===")
        print(f"Foods type: {type(foods)}")
        print(f"Foods length: {len(foods)}")
        
        if foods:
            print(f"First 3 foods:")
            for i, food in enumerate(foods[:3], 1):
                print(f"{i}. {food}")
        else:
            print("❌ FOODS IS EMPTY!")
            
            # Kiểm tra message
            message = result.get('message', '')
            if 'Đã tìm thấy' in message:
                print(f"⚠️  Message says foods were found but foods array is empty!")
                
                # Tìm số lượng trong message
                import re
                match = re.search(r'Đã tìm thấy (\d+) món', message)
                if match:
                    expected_count = int(match.group(1))
                    print(f"⚠️  Message says {expected_count} foods but array has {len(foods)}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_debug() 