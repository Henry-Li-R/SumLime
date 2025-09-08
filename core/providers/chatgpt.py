from openai import OpenAI
from core.providers.base import LLMProvider
import os

# [ ] Not implemented
class ChatGPTProvider(LLMProvider):
    def __init__(self):
        api_key = os.environ.get("CHATGPT_API_KEY")
        if not api_key:
            raise ValueError("CHATGPT_API_KEY value not set in environment variables")

        self.client = OpenAI(api_key=api_key)

    def query(
        self,
        prompt: str,
        chat_turn: int,
        chat_session: int,
        is_summarizing: bool = False,
        system_message="",
    ):
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ]
        with self.client.responses.stream(
            model="gpt-4o-mini",
            input=messages,
        ) as stream:
            for event in stream:
                if event.type == "response.output_text.delta":
                    if event.delta:
                        yield event.delta
            stream.get_final_response()
