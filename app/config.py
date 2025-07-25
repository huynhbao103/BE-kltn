from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
print(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

# Tạo driver kết nối
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "test")

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")

print(f"MongoDB URI: {MONGODB_URI}")
print(f"MongoDB Database: {MONGODB_DB}")

# Tạo MongoDB client
try:
    mongo_client = MongoClient(MONGODB_URI)
    # Test kết nối
    mongo_client.admin.command('ping')
    print("✅ MongoDB kết nối thành công!")
    
    mongo_db = mongo_client[MONGODB_DB]
    print(f"✅ Database '{MONGODB_DB}' đã sẵn sàng")
    
except Exception as e:
    print(f"❌ Lỗi kết nối MongoDB: {e}")
    mongo_client = None
    mongo_db = None
