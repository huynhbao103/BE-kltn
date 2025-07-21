import os
import requests
from typing import Optional

class LLMService:
    """
    Service để gọi LLM API
    """
    
    @staticmethod
    def get_completion(prompt: str, model: str = "gpt-4o") -> str:
        """
        Gọi LLM API để lấy completion
        """
        try:
            # Sử dụng OpenAI API hoặc API tương tự
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                # Fallback: trả về prompt gốc nếu không có API key
                print("WARNING: No OpenAI API key found, returning original prompt")
                return prompt
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "Bạn là một chuyên gia dinh dưỡng và ẩm thực."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 2000,
                "temperature": 0.1
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"LLM API error: {response.status_code} - {response.text}")
                return prompt
                
        except Exception as e:
            print(f"LLM service error: {e}")
            return prompt
    
    @staticmethod
    def get_completion_simple(prompt: str) -> str:
        """
        Phiên bản đơn giản không cần API key
        """
        # Fallback: trả về prompt gốc
        print("INFO: Using simple LLM fallback")
        return prompt 