#!/usr/bin/env python3
"""
Test chi tiết số lượng món ăn cho từng phương pháp nấu
"""

from app.services.neo4j_service import neo4j_service
from app.services.graph_schema_service import GraphSchemaService

def check_all_cooking_methods():
    """Kiểm tra tất cả phương pháp nấu và số lượng món ăn"""
    print("=== Kiểm tra tất cả phương pháp nấu ===\n")
    
    # Lấy tất cả phương pháp nấu
    try:
        cook_methods = neo4j_service.run_query("MATCH (cm:CookMethod) RETURN cm.name as name ORDER BY cm.name")
        print(f"Tổng cộng có {len(cook_methods)} phương pháp nấu:")
        
        total_dishes = 0
        for cm in cook_methods:
            method_name = cm['name']
            
            # Đếm số món ăn cho phương pháp này
            dishes = neo4j_service.run_query("""
            MATCH (cm:CookMethod {name: $method_name})-[:ĐƯỢC_DÙNG_TRONG]->(dish:Dish)
            RETURN count(dish) as count
            """, method_name=method_name)
            
            count = dishes[0]['count'] if dishes else 0
            total_dishes += count
            
            print(f"  - {method_name}: {count} món ăn")
            
            # Hiển thị tên các món ăn (nếu có)
            if count > 0:
                dish_names = neo4j_service.run_query("""
                MATCH (cm:CookMethod {name: $method_name})-[:ĐƯỢC_DÙNG_TRONG]->(dish:Dish)
                RETURN dish.name as name
                ORDER BY dish.name
                """, method_name=method_name)
                
                for dish in dish_names:
                    print(f"    + {dish['name']}")
        
        print(f"\nTổng cộng: {total_dishes} món ăn có phương pháp nấu")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    
    print()

def test_specific_cooking_methods():
    """Test các phương pháp nấu cụ thể"""
    print("=== Test các phương pháp nấu cụ thể ===\n")
    
    test_methods = ["Luộc", "Hấp", "Chiên", "Nướng", "Xào"]
    
    for method in test_methods:
        try:
            foods = GraphSchemaService.get_foods_by_cooking_method(method)
            print(f"{method}: {len(foods)} món ăn")
            
            if foods:
                for food in foods[:5]:  # Chỉ hiển thị 5 món đầu
                    print(f"  - {food['dish_name']}")
                if len(foods) > 5:
                    print(f"  ... và {len(foods) - 5} món khác")
        except Exception as e:
            print(f"Error với {method}: {str(e)}")
        
        print()

def check_dish_without_cooking_method():
    """Kiểm tra món ăn không có phương pháp nấu"""
    print("=== Kiểm tra món ăn không có phương pháp nấu ===\n")
    
    try:
        # Đếm tổng số món ăn
        total_dishes = neo4j_service.run_query("MATCH (d:Dish) RETURN count(d) as count")
        total_count = total_dishes[0]['count']
        
        # Đếm số món ăn có phương pháp nấu
        dishes_with_method = neo4j_service.run_query("""
        MATCH (cm:CookMethod)-[:ĐƯỢC_DÙNG_TRONG]->(dish:Dish)
        RETURN count(DISTINCT dish) as count
        """)
        with_method_count = dishes_with_method[0]['count']
        
        # Đếm số món ăn không có phương pháp nấu
        dishes_without_method = neo4j_service.run_query("""
        MATCH (dish:Dish)
        WHERE NOT EXISTS(()-[:ĐƯỢC_DÙNG_TRONG]->(dish))
        RETURN count(dish) as count
        """)
        without_method_count = dishes_without_method[0]['count']
        
        print(f"Tổng số món ăn: {total_count}")
        print(f"Món ăn có phương pháp nấu: {with_method_count}")
        print(f"Món ăn không có phương pháp nấu: {without_method_count}")
        
        # Hiển thị một số món ăn không có phương pháp nấu
        if without_method_count > 0:
            sample_dishes = neo4j_service.run_query("""
            MATCH (dish:Dish)
            WHERE NOT EXISTS(()-[:ĐƯỢC_DÙNG_TRONG]->(dish))
            RETURN dish.name as name
            LIMIT 10
            """)
            print(f"\nMột số món ăn không có phương pháp nấu:")
            for dish in sample_dishes:
                print(f"  - {dish['name']}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    
    print()

def main():
    """Chạy tất cả các test"""
    print("Checking cooking methods in detail\n")
    
    check_all_cooking_methods()
    test_specific_cooking_methods()
    check_dish_without_cooking_method()
    
    print("Check completed!")

if __name__ == "__main__":
    main() 