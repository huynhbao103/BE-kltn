#!/usr/bin/env python3
"""
Test script để kiểm tra logic xử lý Neo4j khi không có bệnh
"""

def test_medical_conditions_filtering():
    """Test logic lọc bệnh"""
    
    # Test cases
    test_cases = [
        {
            "input": ["Không có"],
            "expected": False,
            "description": "Chỉ có 'Không có'"
        },
        {
            "input": ["Không bệnh"],
            "expected": False,
            "description": "Chỉ có 'Không bệnh'"
        },
        {
            "input": ["Không có bệnh"],
            "expected": False,
            "description": "Chỉ có 'Không có bệnh'"
        },
        {
            "input": ["Bình thường"],
            "expected": False,
            "description": "Chỉ có 'Bình thường'"
        },
        {
            "input": ["Khỏe mạnh"],
            "expected": False,
            "description": "Chỉ có 'Khỏe mạnh'"
        },
        {
            "input": ["Tiểu đường"],
            "expected": True,
            "description": "Có bệnh thực sự"
        },
        {
            "input": ["Tiểu đường", "Không có"],
            "expected": True,
            "description": "Có bệnh và không có bệnh"
        },
        {
            "input": ["Không có", "Tiểu đường"],
            "expected": True,
            "description": "Không có bệnh và có bệnh"
        },
        {
            "input": [],
            "expected": False,
            "description": "Danh sách rỗng"
        },
        {
            "input": None,
            "expected": False,
            "description": "None"
        }
    ]
    
    print("=== Testing Medical Conditions Filtering ===")
    
    for i, test_case in enumerate(test_cases, 1):
        medical_conditions = test_case["input"]
        
        # Logic lọc bệnh (từ code đã sửa)
        has_conditions = False
        real_conditions = []
        
        if medical_conditions:
            for condition in medical_conditions:
                condition_lower = condition.lower().strip()
                if condition_lower not in ["không có", "không bệnh", "không có bệnh", "bình thường", "khỏe mạnh"]:
                    real_conditions.append(condition)
            has_conditions = len(real_conditions) > 0
        
        # Kiểm tra kết quả
        result = "PASS" if has_conditions == test_case["expected"] else "FAIL"
        print(f"{i}. {result} - {test_case['description']}")
        print(f"   Input: {medical_conditions}")
        print(f"   Expected: {test_case['expected']}, Got: {has_conditions}")
        print(f"   Real conditions: {real_conditions}")
        print()

def test_query_logic():
    """Test logic truy vấn"""
    
    print("=== Testing Query Logic ===")
    
    # Test case 1: Không có bệnh, không có emotion, không có cooking method
    print("Test 1: Không có bệnh, không có emotion, không có cooking method")
    medical_conditions = ["Không có"]
    selected_emotion = None
    selected_cooking_methods = []
    
    # Logic lọc bệnh
    has_conditions = False
    if medical_conditions:
        real_conditions = []
        for condition in medical_conditions:
            condition_lower = condition.lower().strip()
            if condition_lower not in ["không có", "không bệnh", "không có bệnh", "bình thường", "khỏe mạnh"]:
                real_conditions.append(condition)
        has_conditions = len(real_conditions) > 0
        medical_conditions = real_conditions
    
    has_emotion = selected_emotion and selected_emotion.strip()
    has_cooking_methods = selected_cooking_methods and len(selected_cooking_methods) > 0
    
    print(f"   Has conditions: {has_conditions}")
    print(f"   Has emotion: {has_emotion}")
    print(f"   Has cooking methods: {has_cooking_methods}")
    
    if not has_conditions and not has_emotion and not has_cooking_methods:
        print("   → Should return query_all_foods()")
    else:
        print("   → Should proceed with specific queries")
    
    print()
    
    # Test case 2: Có bệnh thực sự
    print("Test 2: Có bệnh thực sự")
    medical_conditions = ["Tiểu đường"]
    selected_emotion = None
    selected_cooking_methods = []
    
    # Logic lọc bệnh
    has_conditions = False
    if medical_conditions:
        real_conditions = []
        for condition in medical_conditions:
            condition_lower = condition.lower().strip()
            if condition_lower not in ["không có", "không bệnh", "không có bệnh", "bình thường", "khỏe mạnh"]:
                real_conditions.append(condition)
        has_conditions = len(real_conditions) > 0
        medical_conditions = real_conditions
    
    has_emotion = selected_emotion and selected_emotion.strip()
    has_cooking_methods = selected_cooking_methods and len(selected_cooking_methods) > 0
    
    print(f"   Has conditions: {has_conditions}")
    print(f"   Has emotion: {has_emotion}")
    print(f"   Has cooking methods: {has_cooking_methods}")
    
    if not has_conditions and not has_emotion and not has_cooking_methods:
        print("   → Should return query_all_foods()")
    else:
        print("   → Should proceed with specific queries")
    
    print()
    
    # Test case 3: Không có bệnh nhưng có emotion
    print("Test 3: Không có bệnh nhưng có emotion")
    medical_conditions = ["Không có"]
    selected_emotion = "Vui vẻ"
    selected_cooking_methods = []
    
    # Logic lọc bệnh
    has_conditions = False
    if medical_conditions:
        real_conditions = []
        for condition in medical_conditions:
            condition_lower = condition.lower().strip()
            if condition_lower not in ["không có", "không bệnh", "không có bệnh", "bình thường", "khỏe mạnh"]:
                real_conditions.append(condition)
        has_conditions = len(real_conditions) > 0
        medical_conditions = real_conditions
    
    has_emotion = selected_emotion and selected_emotion.strip()
    has_cooking_methods = selected_cooking_methods and len(selected_cooking_methods) > 0
    
    print(f"   Has conditions: {has_conditions}")
    print(f"   Has emotion: {has_emotion}")
    print(f"   Has cooking methods: {has_cooking_methods}")
    
    if not has_conditions and not has_emotion and not has_cooking_methods:
        print("   → Should return query_all_foods()")
    else:
        print("   → Should proceed with specific queries")
        if not has_conditions:
            print("   → Should get all available foods as base")
        if has_emotion:
            print("   → Should filter by emotion")
        if has_cooking_methods:
            print("   → Should filter by cooking methods")
    
    print()
    
    # Test case 4: Không có bệnh nhưng có cooking method
    print("Test 4: Không có bệnh nhưng có cooking method")
    medical_conditions = ["Bình thường"]
    selected_emotion = None
    selected_cooking_methods = ["Luộc"]
    
    # Logic lọc bệnh
    has_conditions = False
    if medical_conditions:
        real_conditions = []
        for condition in medical_conditions:
            condition_lower = condition.lower().strip()
            if condition_lower not in ["không có", "không bệnh", "không có bệnh", "bình thường", "khỏe mạnh"]:
                real_conditions.append(condition)
        has_conditions = len(real_conditions) > 0
        medical_conditions = real_conditions
    
    has_emotion = selected_emotion and selected_emotion.strip()
    has_cooking_methods = selected_cooking_methods and len(selected_cooking_methods) > 0
    
    print(f"   Has conditions: {has_conditions}")
    print(f"   Has emotion: {has_emotion}")
    print(f"   Has cooking methods: {has_cooking_methods}")
    
    if not has_conditions and not has_emotion and not has_cooking_methods:
        print("   → Should return query_all_foods()")
    else:
        print("   → Should proceed with specific queries")
        if not has_conditions:
            print("   → Should get all available foods as base")
        if has_emotion:
            print("   → Should filter by emotion")
        if has_cooking_methods:
            print("   → Should filter by cooking methods")
    
    print()

if __name__ == "__main__":
    test_medical_conditions_filtering()
    test_query_logic()
    print("=== Test completed ===") 