#!/usr/bin/env python3
"""
Test để kiểm tra logic truy vấn Neo4j mới
"""

from app.graph.nodes.query_neo4j_node import query_neo4j_for_foods, query_popular_foods
from app.services.graph_schema_service import GraphSchemaService
from app.services.neo4j_service import neo4j_service

def test_query_with_no_conditions():
    """Test truy vấn khi không có tình trạng bệnh"""
    print("=== Test truy vấn khi không có tình trạng bệnh ===")
    
    user_data = {
        "medicalConditions": ["Không có"],
        "name": "Test User",
        "age": 25,
        "gender": "Nam"
    }
    
    result = query_neo4j_for_foods(user_data)
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"Total foods: {result['statistics']['total_foods']}")
    print(f"Sources: {list(result['foods'].keys())}")
    print()

def test_query_with_emotion_only():
    """Test truy vấn chỉ với cảm xúc"""
    print("=== Test truy vấn chỉ với cảm xúc ===")
    
    user_data = {
        "medicalConditions": ["Không có"],
        "name": "Test User",
        "age": 25,
        "gender": "Nam"
    }
    
    result = query_neo4j_for_foods(user_data, selected_emotion="Vui vẻ")
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"Total foods: {result['statistics']['total_foods']}")
    print(f"Emotions checked: {result['emotions_checked']}")
    print(f"Sources: {list(result['foods'].keys())}")
    print()

def test_query_with_cooking_method_only():
    """Test truy vấn chỉ với phương pháp nấu"""
    print("=== Test truy vấn chỉ với phương pháp nấu ===")
    
    user_data = {
        "medicalConditions": ["Không có"],
        "name": "Test User",
        "age": 25,
        "gender": "Nam"
    }
    
    result = query_neo4j_for_foods(user_data, selected_cooking_methods=["Luộc", "Hấp"])
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"Total foods: {result['statistics']['total_foods']}")
    print(f"Cooking methods checked: {result['cooking_methods_checked']}")
    print(f"Sources: {list(result['foods'].keys())}")
    print()

def test_query_with_condition_only():
    """Test truy vấn chỉ với tình trạng bệnh"""
    print("=== Test truy vấn chỉ với tình trạng bệnh ===")
    
    user_data = {
        "medicalConditions": ["Tiểu đường"],
        "name": "Test User",
        "age": 25,
        "gender": "Nam"
    }
    
    result = query_neo4j_for_foods(user_data)
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"Total foods: {result['statistics']['total_foods']}")
    print(f"Conditions checked: {result['conditions_checked']}")
    print(f"Sources: {list(result['foods'].keys())}")
    print()

def test_query_with_all_factors():
    """Test truy vấn với tất cả yếu tố"""
    print("=== Test truy vấn với tất cả yếu tố ===")
    
    user_data = {
        "medicalConditions": ["Tiểu đường"],
        "name": "Test User",
        "age": 25,
        "gender": "Nam"
    }
    
    result = query_neo4j_for_foods(
        user_data, 
        selected_emotion="Vui vẻ",
        selected_cooking_methods=["Luộc", "Hấp"]
    )
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"Total foods: {result['statistics']['total_foods']}")
    print(f"Conditions checked: {result['conditions_checked']}")
    print(f"Emotions checked: {result['emotions_checked']}")
    print(f"Cooking methods checked: {result['cooking_methods_checked']}")
    print(f"Sources: {list(result['foods'].keys())}")
    print()

def test_popular_foods():
    """Test truy vấn thực phẩm phổ biến"""
    print("=== Test truy vấn thực phẩm phổ biến ===")
    
    result = query_popular_foods()
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"Total foods: {result['statistics']['total_foods']}")
    print(f"Sources: {list(result['foods'].keys())}")
    print()

def test_graph_schema_methods():
    """Test các method của GraphSchemaService"""
    print("=== Test GraphSchemaService methods ===")
    
    # Test get_foods_by_emotion
    try:
        emotion_foods = GraphSchemaService.get_foods_by_emotion("Vui vẻ")
        print(f"Foods by emotion 'Vui vẻ': {len(emotion_foods)} items")
    except Exception as e:
        print(f"Error getting foods by emotion: {str(e)}")
    
    # Test get_foods_by_cooking_method
    try:
        cooking_foods = GraphSchemaService.get_foods_by_cooking_method("Luộc")
        print(f"Foods by cooking method 'Luộc': {len(cooking_foods)} items")
    except Exception as e:
        print(f"Error getting foods by cooking method: {str(e)}")
    
    # Test get_popular_foods
    try:
        popular_foods = GraphSchemaService.get_popular_foods(5)
        print(f"Popular foods: {len(popular_foods)} items")
    except Exception as e:
        print(f"Error getting popular foods: {str(e)}")
    
    print()

def main():
    """Chạy tất cả các test"""
    print("Testing Neo4j query logic\n")
    
    # Test các trường hợp khác nhau
    test_query_with_no_conditions()
    test_query_with_emotion_only()
    test_query_with_cooking_method_only()
    test_query_with_condition_only()
    test_query_with_all_factors()
    test_popular_foods()
    test_graph_schema_methods()
    
    print("Test completed!")

if __name__ == "__main__":
    main() 