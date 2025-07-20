import sys
sys.path.append('.')
from app.services.graph_schema_service import GraphSchemaService
from app.services.mongo_service import mongo_service

def sync_dishes_neo4j_to_mongo():
    # Lấy danh sách món ăn từ Neo4j
    dishes = GraphSchemaService.get_all_foods_for_healthy_person()
    print(f"Đã lấy {len(dishes)} món ăn từ Neo4j.")

    # Lưu từng món vào MongoDB (upsert theo dish_id)
    upserted = 0
    for dish in dishes:
        doc = {
            "dish_id": dish.get("dish_id"),
            "dish_name": dish.get("dish_name"),
        }
        # Upsert vào MongoDB
        result = mongo_service.db.dishes.update_one(
            {"dish_id": doc["dish_id"]},
            {"$set": doc},
            upsert=True
        )
        upserted += 1
        print(f"Đã upsert: {doc['dish_name']} ({doc['dish_id']})")
    print(f"Tổng số món đã upsert vào MongoDB: {upserted}")

if __name__ == "__main__":
    sync_dishes_neo4j_to_mongo()