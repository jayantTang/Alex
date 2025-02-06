import requests
import json
from typing import Union, Iterator, Callable
import threading


class OllamaAPI:
    def __init__(self, model_name: str, base_url: str = "http://localhost:11434"):
        """
        初始化 Ollama API 客户端。

        :param model_name: 模型名称（如 "deepseek-r1:14b"）。
        :param base_url: Ollama API 的基础地址，默认为 "http://localhost:11434"。
        """
        self.model_name = model_name
        self.base_url = base_url
        self.stream_thread = None
        self.stop_stream_flag = False

    def generate(self, prompt: str, stream: bool = False, temperature: float = 0.7, max_tokens: int = 500) -> Union[str, Iterator[str]]:
        """
        生成文本，支持流式和非流式模式。

        :param prompt: 输入的提示词。
        :param stream: 是否启用流式输出，默认为 False。
        :param temperature: 控制生成随机性的参数，默认为 0.7。
        :param max_tokens: 生成文本的最大长度，默认为 500。
        :return: 如果 stream=True，返回生成器；否则返回完整文本。
        """
        url = f"{self.base_url}/api/generate"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = requests.post(url, headers=headers, json=payload, stream=stream)

        if response.status_code != 200:
            self.handle_error(Exception(f"请求失败，状态码：{response.status_code}"))

        if stream:
            return self._stream_response(response)
        else:
            return response.json().get("response", "")

    def generate_stream(self, prompt: str, callback: Callable[[str], None], temperature: float = 0.7, max_tokens: int = 500) -> None:
        """
        流式生成文本，并通过回调函数实时返回生成内容。

        :param prompt: 输入的提示词。
        :param callback: 回调函数，用于处理实时生成的文本。
        :param temperature: 控制生成随机性的参数，默认为 0.7。
        :param max_tokens: 生成文本的最大长度，默认为 500。
        """
        self.stop_stream_flag = False
        self.stream_thread = threading.Thread(
            target=self._stream_with_callback,
            args=(prompt, callback, temperature, max_tokens),
        )
        self.stream_thread.start()

    def stop_stream(self) -> None:
        """
        主动终止当前的流式生成过程。
        """
        self.stop_stream_flag = True
        if self.stream_thread:
            self.stream_thread.join()

    def _stream_response(self, response: requests.Response) -> Iterator[str]:
        """
        处理流式响应，返回生成器。

        :param response: 流式响应对象。
        :return: 生成器，逐行返回生成的文本。
        """
        for line in response.iter_lines():
            if self.stop_stream_flag:
                break
            if line:
                try:
                    data = line.decode("utf-8")
                    result = json.loads(data)
                    if "response" in result:
                        yield result["response"]
                except json.JSONDecodeError as e:
                    self.handle_error(e)

    def _stream_with_callback(self, prompt: str, callback: Callable[[str], None], temperature: float, max_tokens: int) -> None:
        """
        内部方法：流式生成文本并通过回调函数返回。

        :param prompt: 输入的提示词。
        :param callback: 回调函数，用于处理实时生成的文本。
        :param temperature: 控制生成随机性的参数。
        :param max_tokens: 生成文本的最大长度。
        """
        url = f"{self.base_url}/api/generate"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": True,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = requests.post(url, headers=headers, json=payload, stream=True)

        if response.status_code != 200:
            self.handle_error(Exception(f"请求失败，状态码：{response.status_code}"))

        for line in response.iter_lines():
            if self.stop_stream_flag:
                break
            if line:
                try:
                    data = line.decode("utf-8")
                    result = json.loads(data)
                    if "response" in result:
                        callback(result["response"])
                except json.JSONDecodeError as e:
                    self.handle_error(e)

    def handle_error(self, error: Exception) -> None:
        """
        统一的错误处理方法。

        :param error: 异常对象。
        """
        print(f"发生错误: {error}")
        # 这里可以扩展为记录日志或抛出异常


# 示例用法
if __name__ == "__main__":
    def stream_callback(text: str):
        print(text, end="|", flush=True)

    ollama = OllamaAPI(model_name="deepseek-r1:14b")

    # 非流式生成
    result = ollama.generate("你好", stream=False)
    print("非流式结果:", result)

    # 流式生成
    print("\n\n\n流式结果:")
    ollama.generate_stream("你好", stream_callback)
    # 模拟外部终止
    import time
    time.sleep(20)
    ollama.stop_stream()
