from base import LLMProvider
import os
import requests

class DeepSeekProvider(LLMProvider):
    API_URL = "https://api.deepseek.com/chat/completions"  # adjust if different
    API_KEY = os.environ.get("DEEPSEEK_API_KEY")

    def query(self, prompt: str) -> str:
        """Query DeepSeek model with the claim and return its verdict and rationale."""
        headers = {"Authorization": f"Bearer {DeepSeekProvider.API_KEY}", "Content-Type": "application/json"}
        data = {
            "model": "deepseek-chat",  # replace if needed
            "messages": [{"role": "user", "content": prompt}]
        }
        response = requests.post(DeepSeekProvider.API_URL, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]