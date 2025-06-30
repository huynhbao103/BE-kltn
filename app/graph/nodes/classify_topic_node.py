import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def check_mode(user_question: str) -> str:
    prompt = f"""
Câu sau có thuộc chủ đề dinh dưỡng, món ăn, sức khỏe hoặc bệnh lý không?
Trả lời duy nhất "yes" hoặc "no".
Câu hỏi: "{user_question}"
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Bạn là một trình phân loại chủ đề."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
    )

    answer = response.choices[0].message.content.strip().lower()
    return answer if answer in ("yes", "no") else "invalid"