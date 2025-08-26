from openai import OpenAI
from core.providers.base import LLMProvider
import os


class ChatGPTProvider(LLMProvider):
    def __init__(self):
        api_key = os.environ.get("CHATGPT_API_KEY")
        if not api_key:
            raise ValueError("CHATGPT_API_KEY value not set in environment variables")

        self.client = OpenAI(api_key=api_key)

    def query(self, prompt: str, system_message="") -> str:
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ]
        response = self.client.responses.create(
            model="gpt-4o-mini",
            input=messages,
        )
        return response.output_text
