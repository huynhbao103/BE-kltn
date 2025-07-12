import os
import sys
sys.path.append('.')

from app.graph.nodes.rerank_foods_node import rerank_foods

# Test data
test_state = {
    "user_data": {
        "name": "Test User",
        "age": 25,
        "medicalConditions": ["Không có"]
    },
    "bmi_result": {
        "bmi_category": "Bình thường"
    },
    "selected_emotion": "Vui vẻ",
    "selected_cooking_methods": ["Luộc", "Xào"],
    "aggregated_result": {
        "status": "success",
        "aggregated_foods": [
            {
                "dish_id": "1",
                "dish_name": "Cơm gà",
                "cook_method": "Luộc",
                "diet_name": "Mặn"
            },
            {
                "dish_id": "2", 
                "dish_name": "Rau muống xào",
                "cook_method": "Xào",
                "diet_name": "Chay"
            },
            {
                "dish_id": "3",
                "dish_name": "Phở bò",
                "cook_method": "Luộc", 
                "diet_name": "Mặn"
            },
            {
                "dish_id": "4",
                "dish_name": "Canh chua cá",
                "cook_method": "Nấu",
                "diet_name": "Mặn"
            }
        ]
    },
    "question": "Tôi muốn ăn món chay"
}

print("=== TESTING RERANK NODE ===")
print(f"Question: {test_state['question']}")
print(f"Original foods: {[f['dish_name'] for f in test_state['aggregated_result']['aggregated_foods']]}")

# Test rerank
result = rerank_foods(test_state)

print("\n=== RESULT ===")
print(f"Status: {result.get('rerank_result', {}).get('status')}")
print(f"Message: {result.get('rerank_result', {}).get('message')}")
print(f"Total count: {result.get('rerank_result', {}).get('total_count', 0)}")

ranked_foods = result.get('rerank_result', {}).get('ranked_foods', [])
print(f"Ranked foods: {[f.get('dish_name', 'Unknown') for f in ranked_foods]}") 