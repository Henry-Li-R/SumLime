from anthropic import Anthropic
from core.providers.base import LLMProvider
import os

class ClaudeProvider(LLMProvider):
    def __init__(self):
        api_key = os.environ.get("CLAUDE_API_KEY")
        if not api_key:
            raise ValueError("CLAUDE_API_KEY value not set in environment variables")
        
        self.client = Anthropic(api_key=api_key)

    def query(self, prompt: str) -> str:
        message = [{
            "role": "user",
            "content": [{"type": "text", "text": prompt}],
        }]

        response = self.client.messages.create(
            model='claude-3-haiku-20240307',
            max_tokens=1000,
            temperature=1,
            system=self.SYSTEM_MESSAGE,
            messages=message
        )
        return response.content