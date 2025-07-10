from app.config import driver
from app.services.graph_schema_service import GraphSchemaService

def test_bmi_data():
    """Test dữ liệu BMI trong Neo4j"""
    print("=== TEST BMI DATA IN NEO4J ===")
    
    with driver.session() as session:
        # 1. Kiểm tra có node BMI không
        print("\n1. Kiểm tra node BMI:")
        result = session.run("MATCH (b:BMI) RETURN b.name as name, b LIMIT 10")
        bmi_nodes = [record.data() for record in result]
        print(f"Found {len(bmi_nodes)} BMI nodes:")
        for node in bmi_nodes:
            print(f"  - {node}")
        
        # 2. Kiểm tra relationship PHÙ_HỢP_VỚI_BMI
        print("\n2. Kiểm tra relationship PHÙ_HỢP_VỚI_BMI:")
        result = session.run("MATCH ()-[r:PHÙ_HỢP_VỚI_BMI]->() RETURN count(r) as count")
        count = result.single()["count"]
        print(f"Found {count} PHÙ_HỢP_VỚI_BMI relationships")
        
        # 3. Kiểm tra món ăn có relationship với BMI
        print("\n3. Kiểm tra món ăn có relationship với BMI:")
        result = session.run("""
            MATCH (dish:Dish)-[:PHÙ_HỢP_VỚI_BMI]->(bmi:BMI)
            RETURN dish.name as dish_name, bmi.name as bmi_name
            LIMIT 10
        """)
        foods = [record.data() for record in result]
        print(f"Found {len(foods)} dishes with BMI relationships:")
        for food in foods:
            print(f"  - {food['dish_name']} -> {food['bmi_name']}")
        
        # 4. Test query cụ thể cho "Béo phì"
        print("\n4. Test query cho 'Béo phì':")
        result = session.run("""
            MATCH (dish:Dish)-[:PHÙ_HỢP_VỚI_BMI]->(bmi:BMI {name: 'Béo phì'})
            RETURN dish.name as dish_name, dish.id as dish_id
            LIMIT 10
        """)
        bmi_foods = [record.data() for record in result]
        print(f"Found {len(bmi_foods)} foods for 'Béo phì':")
        for food in bmi_foods:
            print(f"  - {food['dish_name']} (ID: {food['dish_id']})")
        
        # 5. Kiểm tra tất cả relationship types
        print("\n5. Tất cả relationship types:")
        result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType")
        rel_types = [record["relationshipType"] for record in result]
        print("Relationship types:", rel_types)
        
        # 6. Kiểm tra tất cả node labels
        print("\n6. Tất cả node labels:")
        result = session.run("CALL db.labels() YIELD label RETURN label")
        labels = [record["label"] for record in result]
        print("Node labels:", labels)
        
        # 7. Kiểm tra phân bố BMI relationships
        print("\n7. Phân bố BMI relationships:")
        result = session.run("""
            MATCH (dish:Dish)-[:PHÙ_HỢP_VỚI_BMI]->(bmi:BMI)
            RETURN bmi.name as bmi_name, count(dish) as dish_count
            ORDER BY dish_count DESC
        """)
        bmi_distribution = [record.data() for record in result]
        print("BMI distribution:")
        for item in bmi_distribution:
            print(f"  - {item['bmi_name']}: {item['dish_count']} dishes")
        
        # 8. Kiểm tra tên chính xác của BMI nodes
        print("\n8. Tên chính xác của BMI nodes:")
        result = session.run("MATCH (b:BMI) RETURN b.name as name")
        bmi_names = [record["name"] for record in result]
        print("BMI names:", bmi_names)
        
        # 9. Test với tên chính xác
        print("\n9. Test với tên chính xác 'béo phì':")
        result = session.run("""
            MATCH (dish:Dish)-[:PHÙ_HỢP_VỚI_BMI]->(bmi:BMI {name: 'béo phì'})
            RETURN dish.name as dish_name, dish.id as dish_id
            LIMIT 10
        """)
        bmi_foods = [record.data() for record in result]
        print(f"Found {len(bmi_foods)} foods for 'béo phì':")
        for food in bmi_foods:
            print(f"  - {food['dish_name']} (ID: {food['dish_id']})")

def test_graph_schema_service():
    """Test GraphSchemaService.get_foods_by_bmi"""
    print("\n=== TEST GRAPH SCHEMA SERVICE ===")
    
    # Test với "béo phì" (tên chính xác)
    print("\nTesting get_foods_by_bmi('béo phì'):")
    try:
        foods = GraphSchemaService.get_foods_by_bmi("béo phì")
        print(f"Found {len(foods)} foods:")
        for food in foods:
            print(f"  - {food}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test với "thừa cân"
    print("\nTesting get_foods_by_bmi('thừa cân'):")
    try:
        foods = GraphSchemaService.get_foods_by_bmi("thừa cân")
        print(f"Found {len(foods)} foods:")
        for food in foods:
            print(f"  - {food}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_bmi_data()
    test_graph_schema_service()
    driver.close() 