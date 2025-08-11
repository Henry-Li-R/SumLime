from core.providers.base import LLMProvider
from openai import OpenAI
import os

from db import db
from core.providers.models import ChatSession, ChatMessage

class DeepSeekProvider(LLMProvider):

    def __init__(self):
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not set in environment variables")
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    def query(self, prompt: str, chat_session: int, is_summarizing: bool = False, system_message="") -> str:
        
        provider = "summarizer" if is_summarizing else "deepseek"
        
        messages = [
            {"role": "system", "content": system_message},
        ]
        
        prev_messages = ChatMessage.query.filter_by(session_id=chat_session, provider=provider).order_by(ChatMessage.timestamp).all()
        prev_messages_formatted = [{"role": msg.role, "content": msg.content}
                                   for msg in prev_messages]
        messages += prev_messages_formatted
        
        messages.append({"role": "user", "content": prompt})
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=False
        )
        response = response.choices[0].message.content        

        
        # Commit new chat messages to db
        new_prompt = ChatMessage(
            session_id = chat_session,
            provider=provider,
            role="user",
            content=prompt,
        )
        new_response = ChatMessage(
            session_id = chat_session,
            provider=provider,
            role="assistant",
            content=response,
        )
        db.session.add(new_prompt)
        db.session.add(new_response)
        db.session.commit()
        
        return response