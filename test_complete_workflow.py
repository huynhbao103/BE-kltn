#!/usr/bin/env python3
"""
Test toàn bộ workflow với logic mới
"""

from app.graph.engine import run_langgraph_workflow_until_selection, continue_workflow_with_emotion, continue_workflow_with_cooking_method
from app.utils.session_store import save_state_to_redis, load_state_from_redis
import json

def test_workflow_with_no_conditions():
    """Test workflow với user không có tình trạng bệnh"""
    print("=== Test workflow với user không có tình trạng bệnh ===")
    
    # Giả lập user_id (thay thế bằng user_id thật từ MongoDB)
    user_id = "507f1f77bcf86cd799439011"
    question = "Tôi nên ăn gì để tốt cho sức khỏe?"
    
    try:
        # Bước 1: Bắt đầu workflow
        result1 = run_langgraph_workflow_until_selection(user_id, question)
        print(f"Bước 1 - Status: {result1.get('status')}")
        print(f"Bước 1 - Message: {result1.get('message')}")
        
        if result1.get('status') == 'need_emotion':
            session_id = result1.get('session_id')
            print(f"Session ID: {session_id}")
            
            # Bước 2: Chọn cảm xúc
            result2 = continue_workflow_with_emotion(session_id, "Vui vẻ")
            print(f"Bước 2 - Status: {result2.get('status')}")
            print(f"Bước 2 - Message: {result2.get('message')}")
            
            if result2.get('status') == 'need_cooking_method':
                session_id2 = result2.get('session_id')
                
                # Bước 3: Chọn phương pháp nấu
                result3 = continue_workflow_with_cooking_method(session_id2, ["Luộc", "Hấp"])
                print(f"Bước 3 - Status: {result3.get('status')}")
                print(f"Bước 3 - Message: {result3.get('message')}")
                
                if result3.get('status') == 'success':
                    final_result = result3.get('result', {})
                    neo4j_result = final_result.get('neo4j_result', {})
                    print(f"Neo4j Status: {neo4j_result.get('status')}")
                    print(f"Neo4j Message: {neo4j_result.get('message')}")
                    print(f"Total Foods: {neo4j_result.get('statistics', {}).get('total_foods', 0)}")
                    print(f"Sources: {list(neo4j_result.get('foods', {}).keys())}")
        
        print()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print()

def test_workflow_with_conditions():
    """Test workflow với user có tình trạng bệnh"""
    print("=== Test workflow với user có tình trạng bệnh ===")
    
    # Giả lập user_id (thay thế bằng user_id thật từ MongoDB)
    user_id = "507f1f77bcf86cd799439012"
    question = "Tôi nên ăn gì để tốt cho bệnh tiểu đường?"
    
    try:
        # Bước 1: Bắt đầu workflow
        result1 = run_langgraph_workflow_until_selection(user_id, question)
        print(f"Bước 1 - Status: {result1.get('status')}")
        print(f"Bước 1 - Message: {result1.get('message')}")
        
        if result1.get('status') == 'need_emotion':
            session_id = result1.get('session_id')
            print(f"Session ID: {session_id}")
            
            # Bước 2: Chọn cảm xúc
            result2 = continue_workflow_with_emotion(session_id, "Bình thường")
            print(f"Bước 2 - Status: {result2.get('status')}")
            print(f"Bước 2 - Message: {result2.get('message')}")
            
            if result2.get('status') == 'need_cooking_method':
                session_id2 = result2.get('session_id')
                
                # Bước 3: Chọn phương pháp nấu
                result3 = continue_workflow_with_cooking_method(session_id2, ["Luộc"])
                print(f"Bước 3 - Status: {result3.get('status')}")
                print(f"Bước 3 - Message: {result3.get('message')}")
                
                if result3.get('status') == 'success':
                    final_result = result3.get('result', {})
                    neo4j_result = final_result.get('neo4j_result', {})
                    print(f"Neo4j Status: {neo4j_result.get('status')}")
                    print(f"Neo4j Message: {neo4j_result.get('message')}")
                    print(f"Total Foods: {neo4j_result.get('statistics', {}).get('total_foods', 0)}")
                    print(f"Sources: {list(neo4j_result.get('foods', {}).keys())}")
        
        print()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print()

def test_workflow_direct_query():
    """Test truy vấn trực tiếp Neo4j"""
    print("=== Test truy vấn trực tiếp Neo4j ===")
    
    from app.graph.nodes.query_neo4j_node import query_neo4j_for_foods
    
    # Test với user không có bệnh
    user_data_no_condition = {
        "medicalConditions": ["Không có"],
        "name": "Test User 1",
        "age": 25,
        "gender": "Nam"
    }
    
    result1 = query_neo4j_for_foods(user_data_no_condition, "Vui vẻ", ["Luộc", "Hấp"])
    print(f"User không có bệnh:")
    print(f"  Status: {result1['status']}")
    print(f"  Message: {result1['message']}")
    print(f"  Total Foods: {result1['statistics']['total_foods']}")
    print(f"  Sources: {list(result1['foods'].keys())}")
    
    # Test với user có bệnh
    user_data_with_condition = {
        "medicalConditions": ["Tiểu đường"],
        "name": "Test User 2",
        "age": 45,
        "gender": "Nữ"
    }
    
    result2 = query_neo4j_for_foods(user_data_with_condition, "Bình thường", ["Luộc"])
    print(f"\nUser có bệnh:")
    print(f"  Status: {result2['status']}")
    print(f"  Message: {result2['message']}")
    print(f"  Total Foods: {result2['statistics']['total_foods']}")
    print(f"  Sources: {list(result2['foods'].keys())}")
    
    print()

def main():
    """Chạy tất cả các test"""
    print("Testing complete workflow\n")
    
    # Test các trường hợp khác nhau
    test_workflow_direct_query()
    test_workflow_with_no_conditions()
    test_workflow_with_conditions()
    
    print("Test completed!")

if __name__ == "__main__":
    main() 