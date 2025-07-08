import os
from typing import List

def select_cooking_method_node(user_question: str = None) -> dict:
    """
    Node này trả về prompt yêu cầu người dùng chọn phương pháp nấu.
    """
    cooking_methods = [
        "Gỏi",
        "Luộc",
        "Súp",
        "Nướng",
        "Hấp",
        "Chiên",
        "Xào"
    ]
    prompt = "Hãy chọn phương pháp nấu bạn muốn từ danh sách sau: " + ", ".join(cooking_methods) + ". Có thể chọn nhiều phương pháp hoặc chọn tất cả."
    return {
        "prompt": prompt,
        "cooking_methods": cooking_methods
    } 