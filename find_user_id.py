#!/usr/bin/env python3
"""
Tìm user ID thực tế trong database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.mongo_service import mongo_service

def find_real_user_id():
    """Tìm user ID thực tế"""
    
    print("=== FINDING REAL USER ID ===")
    
    try:
        # Lấy tất cả users
        users = mongo_service.get_all_users()
        
        print(f"Total users found: {len(users)}")
        
        if users:
            print("\n=== USERS ===")
            for i, user in enumerate(users[:5], 1):  # Chỉ hiển thị 5 user đầu
                user_id = user.get("_id")
                name = user.get("name", "Unknown")
                age = user.get("age", "N/A")
                medical_conditions = user.get("medicalConditions", [])
                
                print(f"{i}. ID: {user_id}")
                print(f"   Name: {name}")
                print(f"   Age: {age}")
                print(f"   Medical conditions: {medical_conditions}")
                print()
            
            # Lấy user đầu tiên để test
            first_user = users[0]
            user_id = str(first_user.get("_id"))
            
            print(f"=== USING FIRST USER ===")
            print(f"User ID: {user_id}")
            print(f"User data: {first_user}")
            
            return user_id
        else:
            print("❌ No users found in database!")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    find_real_user_id() 