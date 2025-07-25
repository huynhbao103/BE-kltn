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
    def get_foods_by_disease_advanced(disease_name: str, excluded_ids: List[str] = None):
        """Truy vấn nâng cao để tìm thực phẩm theo bệnh"""
        params = {"disease": disease_name}
        query = """
        MATCH (d:Disease {name: $disease})-[:YÊU_CẦU_CHẾ_ĐỘ]->(diet:Diet)
        -[:KHUYẾN_NGHỊ]->(cm:CookMethod)-[:ĐƯỢC_DÙNG_TRONG]->(dish:Dish)
        """
        if excluded_ids:
            query += " WHERE NOT dish.id IN $excluded_ids "
            params["excluded_ids"] = excluded_ids
            
        query += """
        RETURN DISTINCT 
            dish.name AS dish_name, 
            dish.id AS dish_id,
            diet.name AS diet_name,
            cm.name AS cook_method
        ORDER BY dish.name
        """
        with driver.session() as session:
            result = session.run(query, **params)
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
    def get_all_cooking_methods():
        """Lấy tất cả các phương pháp nấu ăn có trong DB."""
        query = "MATCH (cm:CookMethod) RETURN DISTINCT cm.name AS cook_method ORDER BY cook_method"
        with driver.session() as session:
            result = session.run(query)
            return [record["cook_method"] for record in result]

    @staticmethod
    def get_all_relationship_types():
        """Lấy tất cả các loại relationship có trong DB để debug."""
        query = "CALL db.relationshipTypes()"
        with driver.session() as session:
            result = session.run(query)
            return [record["relationshipType"] for record in result]

    @staticmethod
    def get_cook_methods_by_bmi(bmi_category: str):
        """Lấy các phương pháp nấu ăn phù hợp cho một phân loại BMI."""
        # Giả định rằng món ăn phù hợp với BMI thì cách chế biến của nó cũng phù hợp.
        query = """
        MATCH (bmi:BMI) WHERE toLower(bmi.name) = toLower($bmi_category)
        MATCH (bmi)<-[:PHÙ_HỢP_VỚI_BMI]-(dish:Dish)-[:ĐƯỢC_DÙNG_TRONG]->(cm:CookMethod)
        RETURN DISTINCT cm.name AS cook_method
        """
        with driver.session() as session:
            result = session.run(query, bmi_category=bmi_category)
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
    def get_diet_details_by_name(diet_name: str):
        """Lấy chi tiết (tên, mô tả) của một chế độ ăn."""
        query = """
        MATCH (d:Diet {name: $diet_name})
        RETURN d.name AS name, d.description AS description
        LIMIT 1
        """
        with driver.session() as session:
            from neo4j.graph import Node
            record = session.run(query, diet_name=diet_name).single()
            if record and isinstance(record["name"], Node):
                 return record["name"]._properties
            return record.data() if record else None
    
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
    def get_foods_by_emotion(emotion: str, excluded_ids: List[str] = None):
        """Truy vấn thực phẩm phù hợp với cảm xúc"""
        params = {"emotion": emotion}
        query = "MATCH (dish:Dish) "
        
        if excluded_ids:
            query += "WHERE NOT dish.id IN $excluded_ids "
            params["excluded_ids"] = excluded_ids

        query += """
        RETURN DISTINCT 
            dish.name AS dish_name,
            dish.id AS dish_id,
            $emotion AS emotion,
            dish.description AS description
        ORDER BY dish.name
        """
        with driver.session() as session:
            result = session.run(query, **params)
            return [record.data() for record in result]
    
    @staticmethod
    def get_foods_by_cooking_method(cooking_method: str, excluded_ids: List[str] = None):
        """Truy vấn thực phẩm theo phương pháp nấu (không phân biệt hoa thường)"""
        params = {"cooking_method": cooking_method}
        query = """
        MATCH (dish:Dish)-[:ĐƯỢC_DÙNG_TRONG]->(cm:CookMethod)
        WHERE toLower(cm.name) = toLower($cooking_method)
        """
        if excluded_ids:
            query += " AND NOT dish.id IN $excluded_ids "
            params["excluded_ids"] = excluded_ids

        query += """
        RETURN DISTINCT 
            dish.name AS dish_name,
            dish.id AS dish_id,
            cm.name AS cook_method,
            dish.description AS description
        ORDER BY dish.name
        """
        with driver.session() as session:
            result = session.run(query, **params)
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
    
    @staticmethod
    def run_custom_query(query: str, params: Dict[str, Any] = None):
        """Chạy query tùy chỉnh với parameters"""
        if params is None:
            params = {}
        with driver.session() as session:
            result = session.run(query, **params)
            return [record.data() for record in result]
    
    @staticmethod
    def get_foods_by_bmi(bmi_category: str, excluded_ids: List[str] = None):
        """Truy vấn thực phẩm phù hợp với BMI category"""
        params = {"bmi_category": bmi_category}
        query = "MATCH (dish:Dish)-[:PHÙ_HỢP_VỚI_BMI]->(bmi:BMI {name: $bmi_category}) "
        
        if excluded_ids:
            query += "WHERE NOT dish.id IN $excluded_ids "
            params["excluded_ids"] = excluded_ids
            
        query += """
        RETURN DISTINCT 
            dish.name AS dish_name,
            dish.id AS dish_id,
            dish.description AS description,
            bmi.name AS bmi_category
        ORDER BY dish.name
        """
        with driver.session() as session:
            result = session.run(query, **params)
            return [record.data() for record in result]
    
    @staticmethod
    def get_context_and_cook_methods(weather: str, time_of_day: str):
        """
        Lấy context phù hợp từ weather + time_of_day, sau đó lấy danh sách cách chế biến (CookMethod) phù hợp với context đó.
        """
        # Cập nhật dựa trên cấu trúc DB thực tế của bạn
        params = {"weather": weather, "time_of_day": time_of_day}
        
        # Bước 1: Tìm node Context
        context_query = """
            MATCH (w:Weather) WHERE toLower(trim(w.name)) = toLower(trim($weather))
            MATCH (t:TimeOfDay) WHERE toLower(trim(t.name)) = toLower(trim($time_of_day))
            MATCH (w)-[:MÔ_TẢ]->(ctx:Context)<-[:THỜI_ĐIỂM]-(t)
            RETURN ctx.name AS context_name
            
        """
        context_result = GraphSchemaService.run_custom_query(context_query, params)
        context_name = context_result[0]["context_name"] if context_result else None

        # Bước 2: Từ Context, tìm các CookMethod phù hợp
        suggested_cook_methods = []
        if context_name:
            cook_method_query = """
                MATCH (ctx:Context {name: $context_name})-[:PHÙ_HỢP_CHẾ_BIẾNG_BẰNG]->(cm:CookMethod)
                RETURN cm.name AS cook_method
            """
            cook_method_result = GraphSchemaService.run_custom_query(cook_method_query, {"context_name": context_name})
            suggested_cook_methods = [d["cook_method"] for d in cook_method_result]
            
        return context_name, suggested_cook_methods
    
    @staticmethod
    def get_popular_foods(excluded_ids: List[str] = None):
        """Truy vấn các món ăn phổ biến"""
        params = {}
        query = "MATCH (dish:Dish) "
        if excluded_ids:
            query += "WHERE NOT dish.id IN $excluded_ids "
            params["excluded_ids"] = excluded_ids
        
        query += """
          MATCH (dish:Dish)
          RETURN dish.name as dish_name, dish.id as dish_id, dish.description as description
          ORDER BY dish.name
          
        """
        with driver.session() as session:
            result = session.run(query, **params)
            return [record.data() for record in result]