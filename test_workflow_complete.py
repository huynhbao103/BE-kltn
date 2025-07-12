import os
import sys
sys.path.append('.')

from app.graph.engine import run_langgraph_workflow_until_selection, continue_workflow_with_emotion, continue_workflow_with_cooking_method

# Test với user_id thực tế
user_id = "687046cb08b225ef080ef767"  # User thực tế: Bảo Huỳnh
question = "Tôi muốn ăn món chay"

print("=== TESTING COMPLETE WORKFLOW ===")
print(f"User ID: {user_id}")
print(f"Question: {question}")

try:
    # Bước 1: Chạy workflow ban đầu
    print("\n--- Bước 1: Chạy workflow ban đầu ---")
    result = run_langgraph_workflow_until_selection(user_id, question)
    print(f"Status: {result.get('status')}")
    
    if result.get('status') == 'need_emotion':
        print("Workflow cần chọn cảm xúc")
        session_id = result.get('session_id')
        emotion = "Vui vẻ"  # Chọn cảm xúc
        
        # Bước 2: Tiếp tục với cảm xúc
        print(f"\n--- Bước 2: Chọn cảm xúc '{emotion}' ---")
        result = continue_workflow_with_emotion(session_id, emotion)
        print(f"Status: {result.get('status')}")
        
        if result.get('status') == 'need_cooking_method':
            print("Workflow cần chọn phương pháp nấu")
            session_id = result.get('session_id')
            cooking_methods = ["Luộc", "Xào"]  # Chọn phương pháp nấu
            
            # Bước 3: Tiếp tục với phương pháp nấu
            print(f"\n--- Bước 3: Chọn phương pháp nấu {cooking_methods} ---")
            result = continue_workflow_with_cooking_method(session_id, cooking_methods)
            print(f"Status: {result.get('status')}")
            
            # Kết quả cuối cùng
            print(f"\n--- KẾT QUẢ CUỐI CÙNG ---")
            print(f"Message: {result.get('message')}")
            print(f"Total count: {result.get('total_count', 0)}")
            if result.get('foods'):
                print(f"Foods: {[f.get('name', 'Unknown') for f in result.get('foods', [])]}")
            else:
                print("No foods returned")
                
        else:
            print("Workflow completed after emotion selection")
            print(f"Message: {result.get('message')}")
            print(f"Foods count: {result.get('total_count', 0)}")
            
    else:
        print("Workflow completed without emotion selection")
        print(f"Message: {result.get('message')}")
        print(f"Foods count: {result.get('total_count', 0)}")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 