from google import genai
from core.providers.base import LLMProvider
import os

class GeminiProvider(LLMProvider):

    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment variables")
        self.client = genai.Client(api_key=api_key)

    def query(self, prompt: str) -> str:
        messages = [self.SYSTEM_MESSAGE, prompt]
        response = self.client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=messages,
        )
        return response.text