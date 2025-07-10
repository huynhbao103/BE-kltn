from app.config import driver
from typing import List, Dict, Any

class GraphSchemaService:
    """Service để khám phá và làm việc với schema graph hiện tại"""
    
    @staticmethod
    def get_all_node_labels():
        """Lấy tất cả các node labels trong graph"""
        query = """
        CALL db.labels() YIELD label
        RETURN label
        ORDER BY label
        """
        with driver.session() as session:
            result = session.run(query)
            return [record["label"] for record in result]
    
    @staticmethod
    def get_all_relationship_types():
        """Lấy tất cả các relationship types trong graph"""
        query = """
        CALL db.relationshipTypes() YIELD relationshipType
        RETURN relationshipType
        ORDER BY relationshipType
        """
        with driver.session() as session:
            result = session.run(query)
            return [record["relationshipType"] for record in result]
    
    @staticmethod
    def get_node_properties(label: str = None):
        """Lấy properties của các nodes theo label"""
        if label:
            query = f"""
            MATCH (n:{label})
            RETURN DISTINCT keys(n) as properties
            LIMIT 1
            """
            with driver.session() as session:
                result = session.run(query)
                return [record["properties"] for record in result]
        else:
            query = """
            MATCH (n)
            RETURN DISTINCT labels(n) as labels, keys(n) as properties
            """
            with driver.session() as session:
                result = session.run(query)
                return [{"labels": record["labels"], "properties": record["properties"]} for record in result]
    
    @staticmethod
    def get_graph_schema():
        """Lấy toàn bộ schema của graph"""
        schema = {
            "nodes": {},
            "relationships": {},
            "sample_data": {}
        }
        
        # Lấy node labels
        labels = GraphSchemaService.get_all_node_labels()
        for label in labels:
            schema["nodes"][label] = {
                "properties": GraphSchemaService.get_node_properties(label),
                "count": GraphSchemaService.get_node_count(label)
            }
        
        # Lấy relationship types
        rel_types = GraphSchemaService.get_all_relationship_types()
        for rel_type in rel_types:
            schema["relationships"][rel_type] = {
                "count": GraphSchemaService.get_relationship_count(rel_type),
                "connections": GraphSchemaService.get_relationship_connections(rel_type)
            }
        
        # Lấy sample data
        schema["sample_data"] = GraphSchemaService.get_sample_data()
        
        return schema
    
    @staticmethod
    def get_node_count(label: str):
        """Đếm số lượng nodes của một label"""
        query = f"""
        MATCH (n:{label})
        RETURN count(n) as count
        """
        with driver.session() as session:
            result = session.run(query)
            return result.single()["count"]
    
    @staticmethod
    def get_relationship_count(rel_type: str):
        """Đếm số lượng relationships của một type"""
        query = f"""
        MATCH ()-[r:{rel_type}]->()
        RETURN count(r) as count
        """
        with driver.session() as session:
            result = session.run(query)
            return result.single()["count"]
    
    @staticmethod
    def get_relationship_connections(rel_type: str):
        """Lấy thông tin về các kết nối của relationship type"""
        query = f"""
        MATCH (a)-[r:{rel_type}]->(b)
        RETURN DISTINCT labels(a) as from_labels, labels(b) as to_labels, count(r) as count
        ORDER BY count DESC
        """
        with driver.session() as session:
            result = session.run(query)
            return [record.data() for record in result]
    
    @staticmethod
    def get_sample_data():
        """Lấy dữ liệu mẫu từ graph"""
        sample_data = {}
        
        # Lấy sample nodes từ mỗi label
        labels = GraphSchemaService.get_all_node_labels()
        for label in labels:
            query = f"""
            MATCH (n:{label})
            RETURN n
            LIMIT 300
            """
            with driver.session() as session:
                result = session.run(query)
                sample_data[label] = [record["n"] for record in result]
        
        return sample_data
    
    @staticmethod
    def generate_schema_description():
        """Tạo mô tả schema bằng tiếng Việt"""
        schema = GraphSchemaService.get_graph_schema()
        
        description = "## Schema Graph Hiện Tại\n\n"
        
        # Mô tả nodes
        description += "### Nodes (Đỉnh):\n"
        for label, info in schema["nodes"].items():
            count = info["count"]
            description += f"- **{label}**: {count} nodes\n"
            if info["properties"]:
                props = info["properties"][0] if info["properties"] else []
                description += f"  - Properties: {', '.join(props)}\n"
        
        # Mô tả relationships
        description += "\n### Relationships (Quan hệ):\n"
        for rel_type, info in schema["relationships"].items():
            count = info["count"]
            description += f"- **{rel_type}**: {count} relationships\n"
            for conn in info["connections"]:
                from_labels = conn["from_labels"]
                to_labels = conn["to_labels"]
                conn_count = conn["count"]
                description += f"  - {from_labels} -> {to_labels}: {conn_count} connections\n"
        
        return description
    
    @staticmethod
    def get_foods_by_disease_advanced(disease_name: str):
        """Truy vấn nâng cao để tìm thực phẩm theo bệnh"""
        query = """
        MATCH (d:Disease {name: $disease})-[:YÊU_CẦU_CHẾ_ĐỘ]->(diet:Diet)
        -[:KHUYẾN_NGHỊ]->(cm:CookMethod)-[:ĐƯỢC_DÙNG_TRONG]->(dish:Dish)
        RETURN DISTINCT 
            dish.name AS dish_name, 
            dish.id AS dish_id,
            diet.name AS diet_name,
            cm.name AS cook_method
        ORDER BY dish.name
        """
        with driver.session() as session:
            result = session.run(query, disease=disease_name)
            return [record.data() for record in result]
    
    @staticmethod
    def get_diseases_by_food(food_name: str):
        """Tìm các bệnh phù hợp với một món ăn"""
        query = """
        MATCH (d:Disease)-[:YÊU_CẦU_CHẾ_ĐỘ]->(diet:Diet)
        -[:KHUYẾN_NGHỊ]->(cm:CookMethod)-[:ĐƯỢC_DÙNG_TRONG]->(dish:Dish {name: $food_name})
        RETURN DISTINCT d.name AS disease_name
        ORDER BY d.name
        """
        with driver.session() as session:
            result = session.run(query, food_name=food_name)
            return [record["disease_name"] for record in result]
    
    @staticmethod
    def get_cook_methods_by_disease(disease_name: str):
        """Lấy các phương pháp nấu ăn phù hợp cho bệnh"""
        query = """
        MATCH (d:Disease {name: $disease})-[:YÊU_CẦU_CHẾ_ĐỘ]->(diet:Diet)
        -[:KHUYẾN_NGHỊ]->(cm:CookMethod)
        RETURN DISTINCT cm.name AS cook_method
        ORDER BY cm.name
        """
        with driver.session() as session:
            result = session.run(query, disease=disease_name)
            return [record["cook_method"] for record in result]
    
    @staticmethod
    def get_diet_recommendations_by_disease(disease_name: str):
        """Lấy khuyến nghị chế độ ăn cho bệnh"""
        query = """
        MATCH (d:Disease {name: $disease})-[:YÊU_CẦU_CHẾ_ĐỘ]->(diet:Diet)
        RETURN DISTINCT diet.name AS diet_name
        ORDER BY diet.name
        """
        with driver.session() as session:
            result = session.run(query, disease=disease_name)
            return [record["diet_name"] for record in result]
    
    @staticmethod
    def get_food_network_analysis():
        """Phân tích mạng lưới thực phẩm"""
        query = """
        MATCH (d:Disease)-[:YÊU_CẦU_CHẾ_ĐỘ]->(diet:Diet)
        -[:KHUYẾN_NGHỊ]->(cm:CookMethod)-[:ĐƯỢC_DÙNG_TRONG]->(dish:Dish)
        RETURN 
            d.name AS disease,
            diet.name AS diet,
            cm.name AS cook_method,
            dish.name AS dish
        ORDER BY d.name, dish.name
        """
        with driver.session() as session:
            result = session.run(query)
            return [record.data() for record in result]
    
    @staticmethod
    def get_foods_by_emotion(emotion: str):
        """Truy vấn thực phẩm phù hợp với cảm xúc"""
        # Fallback: trả về tất cả món ăn nếu không có relationship với emotion
        query = """
        MATCH (dish:Dish)
        RETURN DISTINCT 
            dish.name AS dish_name,
            dish.id AS dish_id,
            $emotion AS emotion,
            dish.description AS description
        ORDER BY dish.name
        """
        with driver.session() as session:
            result = session.run(query, emotion=emotion)
            return [record.data() for record in result]
    
    @staticmethod
    def get_foods_by_cooking_method(cooking_method: str):
        """Truy vấn thực phẩm theo phương pháp nấu (không phân biệt hoa thường)"""
        query = """
        MATCH (cm:CookMethod)
        WHERE toLower(cm.name) = toLower($cooking_method)
        MATCH (cm)-[:ĐƯỢC_DÙNG_TRONG]->(dish:Dish)
        RETURN DISTINCT 
            dish.name AS dish_name,
            dish.id AS dish_id,
            cm.name AS cook_method,
            dish.description AS description
        ORDER BY dish.name
        """
        with driver.session() as session:
            result = session.run(query, cooking_method=cooking_method)
            return [record.data() for record in result]
    
    @staticmethod
    def get_popular_foods(limit: int = None):
        """Truy vấn thực phẩm phổ biến"""
        if limit:
            query = """
            MATCH (dish:Dish)
            RETURN DISTINCT 
                dish.name AS dish_name,
                dish.id AS dish_id,
                dish.description AS description
            ORDER BY dish.name
            LIMIT $limit
            """
            with driver.session() as session:
                result = session.run(query, limit=limit)
                return [record.data() for record in result]
        else:
            query = """
            MATCH (dish:Dish)
            RETURN DISTINCT 
                dish.name AS dish_name,
                dish.id AS dish_id,
                dish.description AS description
            ORDER BY dish.name
            """
            with driver.session() as session:
                result = session.run(query)
                return [record.data() for record in result]
    
    @staticmethod
    def get_healthy_foods(limit: int = None):
        """Truy vấn thực phẩm tốt cho sức khỏe"""
        if limit:
            query = """
            MATCH (dish:Dish)
            RETURN DISTINCT 
                dish.name AS dish_name,
                dish.id AS dish_id,
                dish.description AS description
            ORDER BY dish.name
            LIMIT $limit
            """
            with driver.session() as session:
                result = session.run(query, limit=limit)
                return [record.data() for record in result]
        else:
            query = """
            MATCH (dish:Dish)
            RETURN DISTINCT 
                dish.name AS dish_name,
                dish.id AS dish_id,
                dish.description AS description
            ORDER BY dish.name
            """
            with driver.session() as session:
                result = session.run(query)
                return [record.data() for record in result]
    
    @staticmethod
    def get_all_foods_for_healthy_person(limit: int = None):
        """Truy vấn tất cả món ăn cho người khỏe mạnh (không có bệnh)"""
        if limit:
            query = """
            MATCH (dish:Dish)
            OPTIONAL MATCH (dish)-[:ĐƯỢC_DÙNG_TRONG]-(di:Diet)
            OPTIONAL MATCH (dish)-[:ĐƯỢC_CHẾ_BIẾN_BẰNG]->(cm:CookMethod)
            RETURN DISTINCT 
                dish.name AS dish_name,
                dish.id AS dish_id,
                dish.description AS description,
                COALESCE(di.name, 'Không xác định') AS diet_name,
                COALESCE(cm.name, 'Không xác định') AS cook_method
            ORDER BY dish.name
            LIMIT $limit
            """
            with driver.session() as session:
                result = session.run(query, limit=limit)
                return [record.data() for record in result]
        else:
            query = """
            MATCH (dish:Dish)
            OPTIONAL MATCH (dish)-[:ĐƯỢC_DÙNG_TRONG]-(di:Diet)
            OPTIONAL MATCH (dish)-[:ĐƯỢC_CHẾ_BIẾN_BẰNG]->(cm:CookMethod)
            RETURN DISTINCT 
                dish.name AS dish_name,
                dish.id AS dish_id,
                dish.description AS description,
                COALESCE(di.name, 'Không xác định') AS diet_name,
                COALESCE(cm.name, 'Không xác định') AS cook_method
            ORDER BY dish.name
            """
            with driver.session() as session:
                result = session.run(query)
                return [record.data() for record in result] 