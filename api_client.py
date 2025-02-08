# api_client.py
from PyQt5.QtCore import QThread, pyqtSignal
import requests

from OllamaAPI import OllamaAPI


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

    def get_response_stream(self, prompt):
        """未调通"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "stream": True  # 开启流式响应
        }

        response = requests.post(self.base_url, json=payload, headers=headers, stream=True)
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                line = line.lstrip(b'data: ').decode('utf-8')
                if line == "[DONE]":
                    break
                try:
                    import json
                    data = json.loads(line)
                    if 'choices' in data and data['choices']:
                        delta = data['choices'][0].get('delta', {})
                        content = delta.get('content', '')
                        if content:
                            yield content
                except json.JSONDecodeError:
                    continue


class ChatWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, question, finish_task, parent=None):
        super().__init__(parent)
        self.question = question
        self.finished.connect(finish_task)
        self.ollama = OllamaAPI(model_name="deepseek-r1:14b")

    def run(self):
        # 引用官方API:非流式结果
        # api = DeepSeekAPI()
        # answer = api.get_response(self.question)
        # self.finished.emit(True, answer)

        # 引用官方API:阻塞式流式生成
        # api = DeepSeekAPI()
        # for content in api.get_response_stream(self.question):
        #     self.finished.emit(False, content)
        # self.finished.emit(True, "")

        # 引用本地模型:非流式结果
        # ollama = OllamaAPI(model_name="deepseek-r1:14b")
        # answer = ollama.generate(self.question, stream=False)
        # self.finished.emit(True, "")

        # 引用本地模型:阻塞式流式生成
        for chunk in self.ollama.generate(self.question, stream=True):
            self.finished.emit(False, chunk)

        self.finished.emit(True, "")

    def stop(self):
        self.ollama.stop_stream()

# api = DeepSeekAPI() # 替换为实际API密钥
# print(api.get_response("你好"))
