#!/usr/bin/env python3
"""
Test để kiểm tra schema thực tế của database
"""

from app.services.graph_schema_service import GraphSchemaService
from app.services.neo4j_service import neo4j_service

def check_schema():
    """Kiểm tra schema thực tế"""
    print("=== Kiểm tra Schema Database ===\n")
    
    # 1. Kiểm tra node labels
    print("1. Node Labels:")
    labels = GraphSchemaService.get_all_node_labels()
    for label in labels:
        count = GraphSchemaService.get_node_count(label)
        print(f"  - {label}: {count} nodes")
    
    print()
    
    # 2. Kiểm tra relationship types
    print("2. Relationship Types:")
    rel_types = GraphSchemaService.get_all_relationship_types()
    for rel_type in rel_types:
        count = GraphSchemaService.get_relationship_count(rel_type)
        print(f"  - {rel_type}: {count} relationships")
    
    print()
    
    # 3. Kiểm tra connections của từng relationship
    print("3. Relationship Connections:")
    for rel_type in rel_types:
        connections = GraphSchemaService.get_relationship_connections(rel_type)
        print(f"  - {rel_type}:")
        for conn in connections:
            print(f"    {conn['from_labels']} -> {conn['to_labels']}: {conn['count']} connections")
    
    print()
    
    # 4. Kiểm tra sample data
    print("4. Sample Data:")
    sample_data = GraphSchemaService.get_sample_data()
    for label, nodes in sample_data.items():
        print(f"  - {label}: {len(nodes)} samples")
        if nodes:
            # Lấy properties của node đầu tiên
            first_node = nodes[0]
            props = list(first_node.keys())
            print(f"    Properties: {props}")
    
    print()
    
    # 5. Kiểm tra cụ thể CookMethod và Dish
    print("5. Kiểm tra CookMethod và Dish:")
    
    # Kiểm tra CookMethod nodes
    try:
        cook_methods = neo4j_service.run_query("MATCH (cm:CookMethod) RETURN cm.name as name LIMIT 5")
        print(f"  CookMethod nodes: {len(cook_methods)} found")
        for cm in cook_methods:
            print(f"    - {cm['name']}")
    except Exception as e:
        print(f"  Error getting CookMethod: {str(e)}")
    
    # Kiểm tra Dish nodes
    try:
        dishes = neo4j_service.run_query("MATCH (d:Dish) RETURN d.name as name LIMIT 5")
        print(f"  Dish nodes: {len(dishes)} found")
        for dish in dishes:
            print(f"    - {dish['name']}")
    except Exception as e:
        print(f"  Error getting Dish: {str(e)}")
    
    # Kiểm tra relationship giữa CookMethod và Dish
    try:
        relationships = neo4j_service.run_query("""
        MATCH (cm:CookMethod)-[r]->(d:Dish)
        RETURN type(r) as rel_type, cm.name as cook_method, d.name as dish
        LIMIT 10
        """)
        print(f"  CookMethod-Dish relationships: {len(relationships)} found")
        for rel in relationships:
            print(f"    - {rel['cook_method']} -[{rel['rel_type']}]-> {rel['dish']}")
    except Exception as e:
        print(f"  Error getting CookMethod-Dish relationships: {str(e)}")
    
    print()

def test_cooking_method_queries():
    """Test các query liên quan đến cooking method"""
    print("=== Test Cooking Method Queries ===\n")
    
    # Test 1: Tìm tất cả CookMethod
    print("1. Tất cả CookMethod:")
    try:
        cook_methods = neo4j_service.run_query("MATCH (cm:CookMethod) RETURN cm.name as name")
        print(f"  Found {len(cook_methods)} cooking methods:")
        for cm in cook_methods:
            print(f"    - {cm['name']}")
    except Exception as e:
        print(f"  Error: {str(e)}")
    
    print()
    
    # Test 2: Tìm Dish theo CookMethod
    print("2. Tìm Dish theo CookMethod 'Luộc':")
    try:
        dishes = neo4j_service.run_query("""
        MATCH (cm:CookMethod {name: 'Luộc'})-[:ĐƯỢC_DÙNG_TRONG]->(d:Dish)
        RETURN d.name as dish_name
        """)
        print(f"  Found {len(dishes)} dishes:")
        for dish in dishes:
            print(f"    - {dish['dish_name']}")
    except Exception as e:
        print(f"  Error: {str(e)}")
    
    print()
    
    # Test 3: Tìm tất cả relationships từ CookMethod
    print("3. Tất cả relationships từ CookMethod:")
    try:
        relationships = neo4j_service.run_query("""
        MATCH (cm:CookMethod)-[r]->(target)
        RETURN type(r) as rel_type, labels(target) as target_labels, count(r) as count
        """)
        print(f"  Found {len(relationships)} relationship types:")
        for rel in relationships:
            print(f"    - CookMethod -[{rel['rel_type']}]-> {rel['target_labels']}: {rel['count']} connections")
    except Exception as e:
        print(f"  Error: {str(e)}")
    
    print()

def main():
    """Chạy tất cả các test"""
    print("Checking database schema\n")
    
    check_schema()
    test_cooking_method_queries()
    
    print("Check completed!")

if __name__ == "__main__":
    main() 