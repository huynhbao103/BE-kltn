from app.config import driver

def get_foods_by_condition(condition_name: str):
    query = """
    MATCH (f:Food)-[:GOOD_FOR]->(:Condition {name: $condition})
    OPTIONAL MATCH (f)-[:CONTAINS]->(i:Ingredient)
    RETURN f.name AS food, collect(i.name) AS ingredients
    """
    with driver.session() as session:
        result = session.run(query, condition=condition_name)
        return [record.data() for record in result]
