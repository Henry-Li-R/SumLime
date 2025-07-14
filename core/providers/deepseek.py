from core.providers.base import LLMProvider
from openai import OpenAI
import os

class DeepSeekProvider(LLMProvider):

    def __init__(self):
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not set in environment variables")
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    def query(self, prompt: str, system_message="") -> str:
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=False
        )
        return response.choices[0].message.content