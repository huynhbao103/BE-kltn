from app.config import driver

class Neo4jService:
    def __init__(self):
        self.driver = driver

    def get_foods_by_condition(self, disease_name: str):
        query = """
         MATCH (d:Disease {name: $disease})-[:YÊU_CẦU_CHẾ_ĐỘ]->(diet:Diet)
          -[:KHUYẾN_NGHỊ]->(cm:CookMethod)-[:ĐƯỢC_DÙNG_TRONG]->(dish:Dish)
        RETURN DISTINCT dish.name AS name, dish.id AS id
        """
        with self.driver.session() as session:
            result = session.run(query, disease=disease_name)
            return [record.data() for record in result]

    def run_query(self, query: str, params: dict = None):
        with self.driver.session() as session:
            result = session.run(query, **(params or {}))
            return [record.data() for record in result]
    
    def get_popular_foods(self, limit: int = None):
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
            with self.driver.session() as session:
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
            with self.driver.session() as session:
                result = session.run(query)
                return [record.data() for record in result]
    
    def get_healthy_foods(self, limit: int = None):
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
            with self.driver.session() as session:
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
            with self.driver.session() as session:
                result = session.run(query)
                return [record.data() for record in result]

# Instance toàn cục để import
neo4j_service = Neo4jService()
