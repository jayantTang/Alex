# api_client.py
import certifi
import requests


class DeepSeekAPI:
    def __init__(self):
        self.api_key = "sk-8284646bfda34cacb37c2ae618e1aabe"
        self.base_url = "https://api.deepseek.com/v1/chat/completions"  # 替换为实际API地址

    def get_response(self, prompt):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }

        response = requests.post(self.base_url, json=payload, headers=headers)
        response.raise_for_status()

        return response.json()["choices"][0]["message"]["content"]


api = DeepSeekAPI() # 替换为实际API密钥
print(api.get_response("你好"))
