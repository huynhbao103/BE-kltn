import os
import sys
sys.path.append('.')

from app.graph.engine import run_langgraph_workflow_until_selection

# Test với user_id thực tế từ MongoDB
user_id = "687046cb08b225ef080ef767"  # User thực tế: Bảo Huỳnh
question = "Tôi muốn ăn món chay"

print("=== TESTING FULL WORKFLOW ===")
print(f"User ID: {user_id}")
print(f"Question: {question}")

try:
    result = run_langgraph_workflow_until_selection(user_id, question)
    
    print("\n=== WORKFLOW RESULT ===")
    print(f"Status: {result.get('status')}")
    
    if result.get('status') == 'need_emotion':
        print("Workflow needs emotion selection")
        print(f"Emotion prompt: {result.get('emotion_prompt')}")
    elif result.get('status') == 'need_cooking_method':
        print("Workflow needs cooking method selection")
        print(f"Cooking method prompt: {result.get('cooking_method_prompt')}")
    else:
        print("Workflow completed")
        print(f"Message: {result.get('message')}")
        print(f"Foods count: {result.get('total_count', 0)}")
        if result.get('foods'):
            print(f"Foods: {[f.get('name', 'Unknown') for f in result.get('foods', [])]}")
        else:
            print("No foods returned")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 