from app.config import driver
from typing import List, Dict, Any
from app.services.mongo_service import mongo_service
from neo4j.graph import Node
import time

class GraphSchemaService:
    """Service để khám phá và làm việc với schema graph hiện tại"""
    
    # Simple in-memory cache
    _cache = {}
    
    @classmethod
    def _get_cache(cls, key: str):
        """Get value from cache if not expired"""
        if key in cls._cache:
            value, timestamp = cls._cache[key]
            if time.time() - timestamp < 3600:  # 1 hour timeout
                return value
            else:
                del cls._cache[key]
        return None
    
    @classmethod
    def _set_cache(cls, key: str, value: Any, timeout: int = 3600):
        """Set value in cache with timeout"""
        cls._cache[key] = (value, time.time())
    
    @classmethod
    def _clear_cache(cls):
        """Clear expired cache entries"""
        current_time = time.time()
        expired_keys = [key for key, (_, timestamp) in cls._cache.items() 
                       if current_time - timestamp > 3600]
        for key in expired_keys:
            del cls._cache[key]
    
    @classmethod
    def clear_cache(cls):
        """Clear all cache entries"""
        cls._cache.clear()
    
    @classmethod
    def get_cache_stats(cls):
        """Get cache statistics"""
        cls._clear_cache()  # Clear expired entries first
        return {
            "total_entries": len(cls._cache),
            "cache_size": sum(len(str(v)) for v in cls._cache.values())
        }
    
    @staticmethod
    def get_all_node_labels():
        """Lấy tất cả các node labels trong graph"""
        # Sử dụng cache để tối ưu hiệu suất
        cache_key = "all_node_labels"
        cached_data = GraphSchemaService._get_cache(cache_key)
        if cached_data:
            return cached_data
        
        query = """
        CALL db.labels() YIELD label
        RETURN label
        ORDER BY label
        """
        try:
            with driver.session() as session:
                result = session.run(query)
                labels = [record["label"] for record in result]
                # Cache kết quả trong 1 giờ
                GraphSchemaService._set_cache(cache_key, labels, timeout=3600)
                return labels
        except Exception as e:
            print(f"Error querying all node labels: {e}")
            return []
    
    @staticmethod
    def get_all_relationship_types():
        """Lấy tất cả các relationship types trong graph"""
        # Sử dụng cache để tối ưu hiệu suất
        cache_key = "all_relationship_types"
        cached_data = GraphSchemaService._get_cache(cache_key)
        if cached_data:
            return cached_data
        
        query = """
        CALL db.relationshipTypes() YIELD relationshipType
        RETURN relationshipType
        ORDER BY relationshipType
        """
        try:
            with driver.session() as session:
                result = session.run(query)
                rel_types = [record["relationshipType"] for record in result]
                # Cache kết quả trong 1 giờ
                GraphSchemaService._set_cache(cache_key, rel_types, timeout=3600)
                return rel_types
        except Exception as e:
            print(f"Error querying all relationship types: {e}")
            return []
    
    @staticmethod
    def get_node_properties(label: str = None):
        """Lấy properties của các nodes theo label"""
        # Sử dụng cache để tối ưu hiệu suất
        cache_key = f"node_properties_{label if label else 'all'}"
        cached_data = GraphSchemaService._get_cache(cache_key)
        if cached_data:
            return cached_data
        
        if label:
            query = f"""
            MATCH (n:{label})
            RETURN DISTINCT keys(n) as properties
            LIMIT 1
            """
            try:
                with driver.session() as session:
                    result = session.run(query)
                    properties = [record["properties"] for record in result]
                    # Cache kết quả trong 1 giờ
                    GraphSchemaService._set_cache(cache_key, properties, timeout=3600)
                    return properties
            except Exception as e:
                print(f"Error querying node properties for {label}: {e}")
                return []
        else:
            query = """
            MATCH (n)
            RETURN DISTINCT labels(n) as labels, keys(n) as properties
            """
            try:
                with driver.session() as session:
                    result = session.run(query)
                    properties = [{"labels": record["labels"], "properties": record["properties"]} for record in result]
                    # Cache kết quả trong 1 giờ
                    GraphSchemaService._set_cache(cache_key, properties, timeout=3600)
                    return properties
            except Exception as e:
                print(f"Error querying all node properties: {e}")
                return []
    
    @staticmethod
    def get_graph_schema():
        """Lấy toàn bộ schema của graph"""
        # Sử dụng cache để tối ưu hiệu suất
        cache_key = "graph_schema"
        cached_data = GraphSchemaService._get_cache(cache_key)
        if cached_data:
            return cached_data
        
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
        
        # Cache kết quả trong 1 giờ
        GraphSchemaService._set_cache(cache_key, schema, timeout=3600)
        return schema
    
    @staticmethod
    def get_node_count(label: str):
        """Đếm số lượng nodes của một label"""
        # Sử dụng cache để tối ưu hiệu suất
        cache_key = f"node_count_{label}"
        cached_data = GraphSchemaService._get_cache(cache_key)
        if cached_data:
            return cached_data
        
        query = f"""
        MATCH (n:{label})
        RETURN count(n) as count
        """
        try:
            with driver.session() as session:
                result = session.run(query)
                count = result.single()["count"]
                # Cache kết quả trong 1 giờ
                GraphSchemaService._set_cache(cache_key, count, timeout=3600)
                return count
        except Exception as e:
            print(f"Error querying node count for {label}: {e}")
            return 0
    
    @staticmethod
    def get_relationship_count(rel_type: str):
        """Đếm số lượng relationships của một type"""
        # Sử dụng cache để tối ưu hiệu suất
        cache_key = f"relationship_count_{rel_type}"
        cached_data = GraphSchemaService._get_cache(cache_key)
        if cached_data:
            return cached_data
        
        query = f"""
        MATCH ()-[r:{rel_type}]->()
        RETURN count(r) as count
        """
        try:
            with driver.session() as session:
                result = session.run(query)
                count = result.single()["count"]
                # Cache kết quả trong 1 giờ
                GraphSchemaService._set_cache(cache_key, count, timeout=3600)
                return count
        except Exception as e:
            print(f"Error querying relationship count for {rel_type}: {e}")
            return 0
    
    @staticmethod
    def get_relationship_connections(rel_type: str):
        """Lấy thông tin về các kết nối của relationship type"""
        # Sử dụng cache để tối ưu hiệu suất
        cache_key = f"relationship_connections_{rel_type}"
        cached_data = GraphSchemaService._get_cache(cache_key)
        if cached_data:
            return cached_data
        
        query = f"""
        MATCH (a)-[r:{rel_type}]->(b)
        RETURN DISTINCT labels(a) as from_labels, labels(b) as to_labels, count(r) as count
        ORDER BY count DESC
        """
        try:
            with driver.session() as session:
                result = session.run(query)
                connections = [record.data() for record in result]
                # Cache kết quả trong 1 giờ
                GraphSchemaService._set_cache(cache_key, connections, timeout=3600)
                return connections
        except Exception as e:
            print(f"Error querying relationship connections for {rel_type}: {e}")
            return []
    
    @staticmethod
    def get_sample_data():
        """Lấy dữ liệu mẫu từ graph"""
        # Sử dụng cache để tối ưu hiệu suất
        cache_key = "sample_data"
        cached_data = GraphSchemaService._get_cache(cache_key)
        if cached_data:
            return cached_data
        
        sample_data = {}
        
        # Lấy sample nodes từ mỗi label
        labels = GraphSchemaService.get_all_node_labels()
        for label in labels:
            query = f"""
            MATCH (n:{label})
            RETURN n
            LIMIT 5
            """
            try:
                with driver.session() as session:
                    result = session.run(query)
                    sample_data[label] = [record["n"] for record in result]
            except Exception as e:
                print(f"Error querying sample data for {label}: {e}")
                sample_data[label] = []
        
        # Cache kết quả trong 1 giờ
        GraphSchemaService._set_cache(cache_key, sample_data, timeout=3600)
        return sample_data
    
    @staticmethod
    def generate_schema_description():
        """Tạo mô tả schema bằng tiếng Việt"""
        # Sử dụng cache để tối ưu hiệu suất
        cache_key = "schema_description"
        cached_data = GraphSchemaService._get_cache(cache_key)
        if cached_data:
            return cached_data
        
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
        
        # Cache kết quả trong 1 giờ
        GraphSchemaService._set_cache(cache_key, description, timeout=3600)
        return description
    
    @staticmethod
    def get_foods_by_disease_advanced(disease_name: str, excluded_ids: List[str] = None):
        """Truy vấn nâng cao để tìm thực phẩm theo bệnh"""
        # Sử dụng cache để tối ưu hiệu suất
        cache_key = f"foods_for_{disease_name}_{hash(str(excluded_ids)) if excluded_ids else 'none'}"
        cached_data = GraphSchemaService._get_cache(cache_key)
        if cached_data:
            return cached_data
        
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
        try:
            with driver.session() as session:
                result = session.run(query, **params)
                foods = [record.data() for record in result]
                # Cache kết quả trong 1 giờ
                GraphSchemaService._set_cache(cache_key, foods, timeout=3600)
                return foods
        except Exception as e:
            print(f"Error querying foods for {disease_name}: {e}")
            return []
    
    @staticmethod
    def get_diseases_by_food(food_name: str):
        """Tìm các bệnh phù hợp với một món ăn"""
        # Sử dụng cache để tối ưu hiệu suất
        cache_key = f"diseases_for_food_{food_name}"
        cached_data = GraphSchemaService._get_cache(cache_key)
        if cached_data:
            return cached_data
        
        query = """
        MATCH (d:Disease)-[:YÊU_CẦU_CHẾ_ĐỘ]->(diet:Diet)
        -[:KHUYẾN_NGHỊ]->(cm:CookMethod)-[:ĐƯỢC_DÙNG_TRONG]->(dish:Dish {name: $food_name})
        RETURN DISTINCT d.name AS disease_name
        ORDER BY d.name
        """
        try:
            with driver.session() as session:
                result = session.run(query, food_name=food_name)
                diseases = [record["disease_name"] for record in result]
                # Cache kết quả trong 1 giờ
                GraphSchemaService._set_cache(cache_key, diseases, timeout=3600)
                return diseases
        except Exception as e:
            print(f"Error querying diseases for food {food_name}: {e}")
            return []
    
    @staticmethod
    def get_cook_methods_by_disease(disease_name: str):
        """Lấy các phương pháp nấu ăn phù hợp cho bệnh"""
        # Sử dụng cache để tối ưu hiệu suất
        cache_key = f"cook_methods_for_{disease_name}"
        cached_data = GraphSchemaService._get_cache(cache_key)
        if cached_data:
            return cached_data
        
        query = """
        MATCH (d:Disease {name: $disease})-[:YÊU_CẦU_CHẾ_ĐỘ]->(diet:Diet)
        -[:KHUYẾN_NGHỊ]->(cm:CookMethod)
        RETURN DISTINCT cm.name AS cook_method
        ORDER BY cm.name
        """
        try:
            with driver.session() as session:
                result = session.run(query, disease=disease_name)
                cook_methods = [record["cook_method"] for record in result]
                # Cache kết quả trong 1 giờ
                GraphSchemaService._set_cache(cache_key, cook_methods, timeout=3600)
                return cook_methods
        except Exception as e:
            print(f"Error querying cook methods for {disease_name}: {e}")
            return []
    
    @staticmethod
    def get_all_cooking_methods():
        """Lấy tất cả các phương pháp nấu ăn có trong DB."""
        # Sử dụng cache để tối ưu hiệu suất
        cache_key = "all_cooking_methods"
        cached_data = GraphSchemaService._get_cache(cache_key)
        if cached_data:
            return cached_data
        
        query = "MATCH (cm:CookMethod) RETURN DISTINCT cm.name AS cook_method ORDER BY cook_method"
        try:
            with driver.session() as session:
                result = session.run(query)
                cook_methods = [record["cook_method"] for record in result]
                # Cache kết quả trong 1 giờ
                GraphSchemaService._set_cache(cache_key, cook_methods, timeout=3600)
                return cook_methods
        except Exception as e:
            print(f"Error querying all cooking methods: {e}")
            return []

    @staticmethod
    def get_cook_methods_by_bmi(bmi_category: str):
        """Lấy các phương pháp nấu ăn phù hợp cho một phân loại BMI."""
        # Sử dụng cache để tối ưu hiệu suất
        cache_key = f"cook_methods_for_bmi_{bmi_category}"
        cached_data = GraphSchemaService._get_cache(cache_key)
        if cached_data:
            return cached_data
        
        # Giả định rằng món ăn phù hợp với BMI thì cách chế biến của nó cũng phù hợp.
        query = """
        MATCH (bmi:BMI) WHERE toLower(bmi.name) = toLower($bmi_category)
        MATCH (bmi)<-[:PHÙ_HỢP_VỚI_BMI]-(dish:Dish)<-[:ĐƯỢC_DÙNG_TRONG]-(cm:CookMethod)
        RETURN DISTINCT cm.name AS cook_method
        """
        try:
            with driver.session() as session:
                result = session.run(query, bmi_category=bmi_category)
                cook_methods = [record["cook_method"] for record in result]
                # Cache kết quả trong 1 giờ
                GraphSchemaService._set_cache(cache_key, cook_methods, timeout=3600)
                return cook_methods
        except Exception as e:
            print(f"Error querying cook methods for BMI {bmi_category}: {e}")
            return []

    @staticmethod
    def get_diet_recommendations_by_disease(disease_name: str):
        """Lấy khuyến nghị chế độ ăn cho bệnh"""
        # Sử dụng cache để tối ưu hiệu suất
        cache_key = f"diet_recs_for_{disease_name}"
        cached_data = GraphSchemaService._get_cache(cache_key)
        if cached_data:
            return cached_data
        
        query = """
        MATCH (d:Disease {name: $disease_name})-[:YÊU_CẦU_CHẾ_ĐỘ]->(diet:Diet)
        RETURN DISTINCT diet.name AS diet_name
        ORDER BY diet.name
        """
        try:
            with driver.session() as session:
                result = session.run(query, disease_name=disease_name)
                diet_names = [record["diet_name"] for record in result]
                # Cache kết quả trong 1 giờ
                GraphSchemaService._set_cache(cache_key, diet_names, timeout=3600)
                return diet_names
        except Exception as e:
            print(f"Error querying diet recommendations for {disease_name}: {e}")
            return []

    @staticmethod
    def get_diet_details_by_name(diet_name: str):
        """Lấy chi tiết (tên, mô tả) của một chế độ ăn."""
        # Sử dụng cache để tối ưu hiệu suất
        cache_key = f"diet_details_{diet_name}"
        cached_data = GraphSchemaService._get_cache(cache_key)
        if cached_data:
            return cached_data
        
        query = """
        MATCH (d:Diet {name: $diet_name})
        RETURN d.name AS name, d.description AS description
        LIMIT 1
        """
        try:
            with driver.session() as session:
                result = session.run(query, diet_name=diet_name).single()
                if result and isinstance(result["name"], Node):
                    diet_details = result["name"]._properties
                else:
                    diet_details = result.data() if result else None
                
                # Cache kết quả trong 1 giờ
                GraphSchemaService._set_cache(cache_key, diet_details, timeout=3600)
                return diet_details
        except Exception as e:
            print(f"Error querying diet details for {diet_name}: {e}")
            return None
    
    @staticmethod
    def get_food_network_analysis():
        """Phân tích mạng lưới thực phẩm"""
        # Sử dụng cache để tối ưu hiệu suất
        cache_key = "food_network_analysis"
        cached_data = GraphSchemaService._get_cache(cache_key)
        if cached_data:
            return cached_data
        
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
        try:
            with driver.session() as session:
                result = session.run(query)
                analysis = [record.data() for record in result]
                # Cache kết quả trong 1 giờ
                GraphSchemaService._set_cache(cache_key, analysis, timeout=3600)
                return analysis
        except Exception as e:
            print(f"Error querying food network analysis: {e}")
            return []
    @staticmethod
    def get_foods_by_cooking_method(cooking_method: str, excluded_ids: List[str] = None):
        """Truy vấn thực phẩm theo phương pháp nấu (không phân biệt hoa thường)"""
        # Sử dụng cache để tối ưu hiệu suất
        cache_key = f"foods_for_cooking_{cooking_method}_{hash(str(excluded_ids)) if excluded_ids else 'none'}"
        cached_data = GraphSchemaService._get_cache(cache_key)
        if cached_data:
            return cached_data
        
        params = {"cooking_method": cooking_method}
        query = """
        MATCH (cm:CookMethod)-[:ĐƯỢC_DÙNG_TRONG]->(dish:Dish)
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
        try:
            with driver.session() as session:
                result = session.run(query, **params)
                foods = [record.data() for record in result]
                # Cache kết quả trong 1 giờ
                GraphSchemaService._set_cache(cache_key, foods, timeout=3600)
                return foods
        except Exception as e:
            print(f"Error querying foods for cooking method {cooking_method}: {e}")
            return []

    
    @staticmethod
    def get_all_foods_for_healthy_person(limit: int = None):
        """Truy vấn tất cả món ăn cho người khỏe mạnh (không có bệnh)"""
        # Sử dụng cache để tối ưu hiệu suất
        cache_key = f"healthy_foods_{limit if limit else 'all'}"
        cached_data = GraphSchemaService._get_cache(cache_key)
        if cached_data:
            return cached_data
        
        if limit:
            query = """
            MATCH (dish:Dish)
            OPTIONAL MATCH (dish)-[:ĐƯỢC_DÙNG_TRONG]-(di:Diet)
            OPTIONAL MATCH (cm:CookMethod)-[:ĐƯỢC_DÙNG_TRONG]->(dish)
            RETURN DISTINCT 
                dish.name AS dish_name,
                dish.id AS dish_id,
                dish.description AS description,
                COALESCE(di.name, 'Không xác định') AS diet_name,
                COALESCE(cm.name, 'Không xác định') AS cook_method
            ORDER BY dish.name
            LIMIT $limit
            """
            try:
                with driver.session() as session:
                    result = session.run(query, limit=limit)
                    foods = [record.data() for record in result]
                    # Cache kết quả trong 1 giờ
                    GraphSchemaService._set_cache(cache_key, foods, timeout=3600)
                    return foods
            except Exception as e:
                print(f"Error querying healthy foods with limit: {e}")
                return []
        else:
            query = """
            MATCH (dish:Dish)
            OPTIONAL MATCH (dish)-[:ĐƯỢC_DÙNG_TRONG]-(di:Diet)
            OPTIONAL MATCH (cm:CookMethod)-[:ĐƯỢC_DÙNG_TRONG]->(dish)
            RETURN DISTINCT 
                dish.name AS dish_name,
                dish.id AS dish_id,
                dish.description AS description,
                COALESCE(di.name, 'Không xác định') AS diet_name,
                COALESCE(cm.name, 'Không xác định') AS cook_method
            ORDER BY dish.name
            """
            try:
                with driver.session() as session:
                    result = session.run(query)
                    foods = [record.data() for record in result]
                    # Cache kết quả trong 1 giờ
                    GraphSchemaService._set_cache(cache_key, foods, timeout=3600)
                    return foods
            except Exception as e:
                print(f"Error querying all healthy foods: {e}")
                return []
    
    @staticmethod
    def run_custom_query(query: str, params: Dict[str, Any] = None):
        """Chạy query tùy chỉnh với parameters"""
        # Chỉ cache cho các query đọc (SELECT, MATCH, CALL db.labels, etc.)
        # Không cache cho các query ghi (CREATE, DELETE, SET, etc.)
        is_read_query = any(keyword in query.upper() for keyword in ['SELECT', 'MATCH', 'CALL', 'RETURN', 'WITH'])
        
        if is_read_query:
            # Tạo cache key từ query và params
            cache_key = f"custom_query_{hash(query + str(sorted(params.items()) if params else []))}"
            cached_data = GraphSchemaService._get_cache(cache_key)
            if cached_data:
                return cached_data
        
        if params is None:
            params = {}
        
        try:
            with driver.session() as session:
                result = session.run(query, **params)
                data = [record.data() for record in result]
                
                # Chỉ cache cho read queries
                if is_read_query:
                    GraphSchemaService._set_cache(cache_key, data, timeout=3600)
                
                return data
        except Exception as e:
            print(f"Error running custom query: {e}")
            return []
    
    @staticmethod
    def get_foods_by_bmi(bmi_category: str, excluded_ids: List[str] = None):
        """Truy vấn thực phẩm phù hợp với BMI category"""
        # Sử dụng cache để tối ưu hiệu suất
        cache_key = f"foods_for_bmi_{bmi_category}_{hash(str(excluded_ids)) if excluded_ids else 'none'}"
        cached_data = GraphSchemaService._get_cache(cache_key)
        if cached_data:
            return cached_data
        
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
        try:
            with driver.session() as session:
                result = session.run(query, **params)
                foods = [record.data() for record in result]
                # Cache kết quả trong 1 giờ
                GraphSchemaService._set_cache(cache_key, foods, timeout=3600)
                return foods
        except Exception as e:
            print(f"Error querying foods for BMI {bmi_category}: {e}")
            return []
    
    @staticmethod
    def get_context_and_cook_methods(weather: str, time_of_day: str):
        """
        Lấy context phù hợp từ weather + time_of_day, sau đó lấy danh sách cách chế biến (CookMethod) phù hợp với context đó.
        """
        # Sử dụng cache để tối ưu hiệu suất
        cache_key = f"context_cook_methods_{weather}_{time_of_day}"
        cached_data = GraphSchemaService._get_cache(cache_key)
        if cached_data:
            return cached_data
        
        # Cập nhật dựa trên cấu trúc DB thực tế của bạn
        params = {"weather": weather, "time_of_day": time_of_day}
        
        # Bước 1: Tìm node Context
        context_query = """
            MATCH (w:Weather) WHERE toLower(trim(w.name)) = toLower(trim($weather))
            MATCH (t:TimeOfDay) WHERE toLower(trim(t.name)) = toLower(trim($time_of_day))
            MATCH (w)-[:MÔ_TẢ]->(ctx:Context)<-[:THỜI_ĐIỂM]-(t)
            RETURN ctx.name AS context_name
            
        """
        try:
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
            
            result = (context_name, suggested_cook_methods)
            # Cache kết quả trong 1 giờ
            GraphSchemaService._set_cache(cache_key, result, timeout=3600)
            return result
        except Exception as e:
            print(f"Error querying context and cook methods: {e}")
            return None, []
    
    @staticmethod
    def get_popular_foods(excluded_ids: List[str] = None):
        """Truy vấn các món ăn phổ biến"""
        # Sử dụng cache để tối ưu hiệu suất
        cache_key = f"popular_foods_{hash(str(excluded_ids)) if excluded_ids else 'none'}"
        cached_data = GraphSchemaService._get_cache(cache_key)
        if cached_data:
            return cached_data
        
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
        try:
            with driver.session() as session:
                result = session.run(query, **params)
                foods = [record.data() for record in result]
                # Cache kết quả trong 1 giờ
                GraphSchemaService._set_cache(cache_key, foods, timeout=3600)
                return foods
        except Exception as e:
            print(f"Error querying popular foods: {e}")
            return []

    @staticmethod
    def get_all_ingredients():
        """Lấy tất cả các thành phần (Ingredient) từ MongoDB."""
        # Sử dụng cache để tối ưu hiệu suất
        cache_key = "all_ingredients"
        cached_data = GraphSchemaService._get_cache(cache_key)
        if cached_data:
            return cached_data
        
        try:
            ingredients = mongo_service.get_all_ingredients()
            # Cache kết quả trong 1 giờ
            GraphSchemaService._set_cache(cache_key, ingredients, timeout=3600)
            return ingredients
        except Exception as e:
            print(f"Error getting all ingredients: {e}")
            return []

    @classmethod
    def get_cook_methods_by_ingredients(cls, ingredients: list) -> list:
        """
        Lấy các phương pháp chế biến phù hợp với danh sách nguyên liệu.
        """
        # Sử dụng cache để tối ưu hiệu suất
        cache_key = f"cook_methods_for_ingredients_{hash(str(sorted(ingredients)))}"
        cached_data = cls._get_cache(cache_key)
        if cached_data:
            return cached_data
        
        try:
            cook_methods = mongo_service.get_cook_methods_by_ingredients(ingredients)
            # Cache kết quả trong 1 giờ
            cls._set_cache(cache_key, cook_methods, timeout=3600)
            return cook_methods
        except Exception as e:
            print(f"Error getting cook methods by ingredients: {e}")
            return []