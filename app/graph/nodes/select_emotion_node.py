import os
from typing import List

def select_emotion_node(user_question: str = None) -> dict:
    """
    Node này trả về prompt yêu cầu người dùng chọn cảm xúc hiện tại của mình.
    """
    emotions = [
        "Vui vẻ",
        "Buồn bã",
        "Bình thường",
        "Tức giận",
        "Mệt mỏi",
        "Hạnh phúc",
        "Trầm cảm",
    ]
    prompt = "Hãy chọn cảm xúc hiện tại của bạn từ danh sách sau: " + ", ".join(emotions) + ". Nếu không có cảm xúc nào phù hợp, hãy chọn 'Bình thường'."
    return {
        "prompt": prompt,
        "emotions": emotions
    } 