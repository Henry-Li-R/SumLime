# run in a Python shell from repo root

from app import app
from db import db
from core.providers.models import ChatSession, ChatTurn, LLMOutput  # forces import

with app.app_context():
    print(sorted(db.metadata.tables.keys()))
    # Expect: ['chats', 'chat_turns', ...]   # whatever your table names are