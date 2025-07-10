import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def check_mode(user_question: str) -> str:
    prompt = f"""Phân loại câu hỏi sau.
Nếu câu hỏi liên quan đến việc gợi ý món ăn, tư vấn dinh dưỡng, hoặc các chủ đề về thực phẩm và sức khỏe, hãy trả lời là "tư vấn".
Nếu không, hãy trả lời là "không liên quan".
Chỉ trả lời duy nhất "tư vấn" hoặc "không liên quan".

Câu hỏi: "{user_question}"
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Bạn là một trợ lý AI chuyên phân loại câu hỏi. Nhiệm vụ của bạn là trả lời 'tư vấn' cho các câu hỏi về thực phẩm/dinh dưỡng và 'không liên quan' cho các câu hỏi khác."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
    )

    answer = response.choices[0].message.content.strip().lower()
    # Đảm bảo kết quả trả về là một trong hai giá trị mong đợi
    if "tư vấn" in answer:
        return "tư vấn"
    return "không liên quan"