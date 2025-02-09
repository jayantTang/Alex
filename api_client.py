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

        content = """</think>

您好！很高兴为您提供服务。如果您有任何问题或需要帮助，请随时告诉我。

>>> 请给出一个简单的python代码示例
<think>
用户之前询问了如何在本地部署生动的AI语音系统，并且现在要求提供一个简单的Python代码示例。

考虑到用户的请求，我应该提供一个基础但完整的例子，涵盖文本生成和语音合成两部分。选择DeepSeek的模型可能不太常见，转而
推荐使用更流行的开源模型，比如VicGpt和pyttsx3，因为它们更容易获取和部署。

同时，需要确保代码简洁明了，并且包含必要的注释，方便用户理解和运行。此外，提醒用户安装所需的库，并注意硬件需求，避免
他们遇到不必要的问题。
</think>

以下是一个简单的Python代码示例，用于实现基于文本的对话生成并输出语音（使用 `pyttsx3` 和 `vicgpt` 模型）：

---

### 1. 安装依赖
首先安装必要的库：
```bash
pip install pyttsx3 vicgpt
```

---

### 2. 示例代码

```python
import os
import pyttsx3
from vicgpt import VicGPT

# 初始化语音合成器
engine = pyttsx3.init()
volume = engine.getProperty('volume')
engine.setProperty('volume', volume - 0.1)  # 调整音量（可选）

# 初始化对话模型（VicGPT）
model_path = os.path.join("vicgpt-1.2.6", "vicgpt")
assistant = VicGPT(model_path, n_ctx=2048, n_threads=4)

# 定义对话函数
def chat_and_speak():
    while True:
        # 用户输入
        user_input = input("您：")
        print("AI思考中...")

        # 生成回复（调整parameters参数可控制输出质量）
        response = assistant.chat(user_input, parameters={"temperature": 0.7, "max_new_tokens": 512})

        # 输出AI的回复
        print(f"AI：{response}")

        # 将文本转换为语音并播放
        engine.say(response)
        engine.runAndWait()

# 运行对话函数
if __name__ == "__main__":
    chat_and_speak()
```

---

### 3. 功能说明：
1. **文本生成**：使用 `VicGPT` 模型生成回复。
2. **语音合成**：使用 `pyttsx3` 将生成的文本转换为语音并播放。

---

### 4. 注意事项
- 如果需要更高性能，可以尝试其他大语言模型（如 `llama-cpp`）。
- 确保本地有足够的计算资源运行这些模型。

如果有任何问题，请随时告诉我！
self.finished.emit(False, chunk)"""

        # for i in range(0, len(content), 3):
        #     chunk = content[i:i + 3]
        #     self.finished.emit(False, chunk)

        self.finished.emit(True, "")

    def stop(self):
        self.ollama.stop_stream()

# api = DeepSeekAPI() # 替换为实际API密钥
# print(api.get_response("你好"))
