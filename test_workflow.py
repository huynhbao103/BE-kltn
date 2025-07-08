#!/usr/bin/env python3
"""
Test script cho workflow hoàn chỉnh
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.graph.engine import run_langgraph_workflow_until_emotion, continue_workflow_with_emotion
from app.services.mongo_service import mongo_service
from app.utils.session_store import save_state_to_redis, load_state_from_redis

def test_workflow():
    """Test workflow hoàn chỉnh từ đầu đến cuối"""
    
    print("=== TEST WORKFLOW HOÀN CHỈNH ===\n")
    
    # Lấy user thực tế từ database
    try:
        users = mongo_service.get_all_users()
        print(f"Tìm thấy {len(users)} users trong database")
        
        if not users:
            print("Không có user nào trong database")
            return
        
        # Lấy user đầu tiên
        user = users[0]
        user_id = str(user["_id"])
        user_name = user.get("name", "Unknown")
        medical_conditions = user.get("medicalConditions", [])
        
        print(f"Test với user: {user_name} (ID: {user_id})")
        print(f"Bệnh lý: {medical_conditions}")
        
        # Bước 1: Chạy workflow đến khi cần cảm xúc
        print("\n1. Chạy workflow ban đầu:")
        result1 = run_langgraph_workflow_until_emotion(
            user_id=user_id,
            question="Tôi nên ăn gì để tốt cho sức khỏe?"
        )
        
        print(f"   → Status: {result1.get('status')}")
        
        if result1.get("status") == "need_emotion":
            print("   → ✅ Cần chọn cảm xúc - đúng như mong đợi")
            session_id = result1["session_id"]
            emotion_prompt = result1["emotion_prompt"]
            print(f"   → Session ID: {session_id}")
            print(f"   → Emotion prompt: {emotion_prompt}")
            
            # Kiểm tra session có được lưu không
            try:
                state = load_state_from_redis(session_id)
                print(f"   → ✅ Session được lưu thành công")
                print(f"   → State step: {state.get('step')}")
            except Exception as e:
                print(f"   → ❌ Lỗi load session: {str(e)}")
                return
            
            # Bước 2: Tiếp tục workflow với cảm xúc
            print("\n2. Tiếp tục với cảm xúc:")
            emotion = "Mệt mỏi"
            print(f"   → Chọn cảm xúc: {emotion}")
            
            result2 = continue_workflow_with_emotion(session_id, emotion)
            print(f"   → Final status: {result2.get('status')}")
            print(f"   → Message: {result2.get('message', '')[:200]}...")
            
            # Kiểm tra các thành phần mới
            print("\n3. Kiểm tra các thành phần mới:")
            
            if result2.get("llm_check"):
                llm_check = result2["llm_check"]
                print(f"   → LLM check: {llm_check.get('response')}")
                print(f"   → LLM reasoning: {llm_check.get('reasoning', '')[:100]}...")
                print(f"   → Foods checked: {llm_check.get('foods_checked', [])[:3]}")
            
            if result2.get("fallback_attempts", 0) > 0:
                print(f"   → Fallback attempts: {result2['fallback_attempts']}")
            
            if result2.get("reranked_data"):
                print("   → ✅ Có dữ liệu đã sắp xếp lại")
                reranked_foods = result2["reranked_data"].get("foods", {})
                for condition, food_data in reranked_foods.items():
                    if isinstance(food_data, dict) and "scores" in food_data:
                        scores = food_data["scores"]
                        print(f"   → Scores cho {condition}: {list(scores.items())[:3]}")
            
            # Kiểm tra neo4j_data
            if result2.get("neo4j_data"):
                neo4j_data = result2["neo4j_data"]
                print(f"   → Neo4j status: {neo4j_data.get('status')}")
                if neo4j_data.get("statistics"):
                    stats = neo4j_data["statistics"]
                    print(f"   → Statistics: {stats}")
            
            print("\n✅ Workflow hoàn thành thành công!")
            
        elif result1.get("status") == "success":
            print("   → Workflow hoàn thành ngay lập tức")
            print(f"   → Message: {result1.get('message', '')[:200]}...")
            
        elif result1.get("status") == "error":
            print(f"   → ❌ Lỗi: {result1.get('message', '')}")
            
        else:
            print(f"   → ❌ Trạng thái không xác định: {result1}")
    
    except Exception as e:
        print(f"❌ Lỗi trong quá trình test: {str(e)}")
        import traceback
        traceback.print_exc()

def test_session_management():
    """Test quản lý session"""
    
    print("\n=== TEST QUẢN LÝ SESSION ===\n")
    
    # Test save và load session
    test_state = {
        "user_id": "test_user",
        "question": "test question",
        "step": "emotion_selected",
        "selected_emotion": "Mệt mỏi"
    }
    
    try:
        # Save session
        session_id = save_state_to_redis(test_state)
        print(f"1. Save session: {session_id}")
        
        # Load session
        loaded_state = load_state_from_redis(session_id)
        print(f"2. Load session: {loaded_state.get('step')}")
        
        # Test với session_id không tồn tại
        try:
            load_state_from_redis("invalid_session")
            print("3. ❌ Lỗi: Không throw exception cho session không tồn tại")
        except Exception as e:
            print(f"3. ✅ Đúng: Throw exception cho session không tồn tại: {str(e)}")
        
        print("✅ Session management hoạt động tốt!")
        
    except Exception as e:
        print(f"❌ Lỗi session management: {str(e)}")

if __name__ == "__main__":
    try:
        # Test session management trước
        test_session_management()
        
        # Test workflow hoàn chỉnh
        test_workflow()
        
    except Exception as e:
        print(f"❌ Lỗi trong quá trình test: {str(e)}")
        import traceback
        traceback.print_exc() 