import os
import sys
sys.path.append('.')

from app.services.mongo_service import mongo_service

# Tìm user đầu tiên trong database
users = mongo_service.get_all_users()
print("=== USERS IN DATABASE ===")
for i, user in enumerate(users[:5]):  # Chỉ hiển thị 5 user đầu
    print(f"{i+1}. ID: {user.get('_id')}")
    print(f"   Name: {user.get('name', 'Unknown')}")
    print(f"   Email: {user.get('email', 'Unknown')}")
    print()

if users:
    first_user = users[0]
    print(f"=== USING FIRST USER ===")
    print(f"User ID: {first_user.get('_id')}")
    print(f"User Name: {first_user.get('name', 'Unknown')}")
else:
    print("No users found in database") 