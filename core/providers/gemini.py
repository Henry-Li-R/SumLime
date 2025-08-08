from google import genai
from core.providers.base import LLMProvider
import os

from db import db
from core.providers.models import ChatSession, ChatMessage

class GeminiProvider(LLMProvider):

    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment variables")
        self.client = genai.Client(api_key=api_key)

    def query(self, prompt: str, chat_session: int | None = None, system_message="") -> str:
        # System message
        messages = [{
                "role": "user", # de facto "system" role
                "parts": [{"text": system_message}]
            }]
        
        # Previous messages
        prev_messages = ChatMessage.query.filter_by(session_id=chat_session, provider="Gemini").order_by(ChatMessage.timestamp).all()
        for msg in prev_messages:
            messages.append({
                "role": msg.role,
                "parts": [{"text": msg.content}]
            })

        # Append user message
        messages.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })
        
        response = self.client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=messages,
        )
        
        # Commit new chat if needed
        if chat_session is None:
            new_session = ChatSession(title="Chat Title")
            db.session.add(new_session)
            db.session.commit()
            chat_session = new_session.id

        # Store user + assistant messages
        db.session.add_all([
            ChatMessage(
                session_id=chat_session,
                provider="gemini",
                role="user",
                content=prompt
            ),
            ChatMessage(
                session_id=chat_session,
                provider="gemini",
                role="model",
                content=response.text
            )
        ])
        db.session.commit()

        return response.text