import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def check_mode(user_question: str) -> str:
    prompt = f"""Phân loại câu hỏi sau.
Nếu câu hỏi liên quan đến việc gợi ý món ăn, tư vấn dinh dưỡng, hoặc các chủ đề về sức khỏe, hãy trả lời là "tư vấn".
Nếu câu hỏi yêu cầu cụ thể về cách chế biến (như chiên, nướng, luộc, hấp, xào, kho, nấu canh, salad, chay, mặn, ngọt, đắng, cay, smoothie, etc,...) hỏi về món khác ngoài các món trên hãy trả lời là "cooking_request".
Nếu câu hỏi yêu cầu hỏi về món khác ( như món khác, món nào khác? tôi không thích món các món này, ect..) hãy trả lời là "cooking_request".
Nếu không, hãy trả lời là "không liên quan".
Chỉ trả lời duy nhất "tư vấn", "cooking_request" hoặc "không liên quan".

Câu hỏi: "{user_question}"
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Bạn là một trợ lý AI chuyên phân loại câu hỏi. Nhiệm vụ của bạn là trả lời 'tư vấn' cho các câu hỏi về thực phẩm/dinh dưỡng, 'cooking_request' cho yêu cầu cụ thể về cách chế biến, và 'không liên quan' cho các câu hỏi khác."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
    )

    answer = response.choices[0].message.content.strip().lower()
    # Đảm bảo kết quả trả về là một trong ba giá trị mong đợi
    if "cooking_request" in answer:
        return "cooking_request"
    elif "tư vấn" in answer:
        return "tư vấn"
    return "không liên quan"

def extract_cooking_methods(user_question: str) -> list:
    """Trích xuất các phương pháp nấu từ câu hỏi của user. Nếu phát hiện các từ khóa như 'tất cả', 'món khác', 'bất kỳ', 'tùy' thì trả về ['ALL']."""
    all_keywords = ["tất cả", "tất cả các món", "món khác", "bất kỳ", "tùy"]
    question_lower = user_question.lower()
    for kw in all_keywords:
        if kw in question_lower:
            return ["ALL"]
    cooking_keywords = {
        "chiên": ["chiên", "rán", "deep fry", "pan fry"],
        "nướng": ["nướng", "grill", "bake", "roast"],
        "luộc": ["luộc", "boil"],
        "hấp": ["hấp", "steam"],
        "xào": ["xào", "stir fry", "sauté"],
        "kho": ["kho", "braise", "stew"],
        "nấu canh": ["nấu canh", "soup", "canh"],
        "salad": ["salad", "gỏi", "trộn"],
        "smoothie": ["smoothie", "sinh tố", "juice"],
        "hầm": ["hầm", "slow cook"],
        "quay": ["quay", "roast"],
        "om": ["om", "braise"],
        "nướng vỉ": ["nướng vỉ", "grill"],
        "nướng lò": ["nướng lò", "bake"],
        "xào khô": ["xào khô", "dry stir fry"],
        "xào ướt": ["xào ướt", "wet stir fry"],
    }
    found_methods = []
    for method, keywords in cooking_keywords.items():
        for keyword in keywords:
            if keyword in question_lower:
                found_methods.append(method)
                break
    return found_methods