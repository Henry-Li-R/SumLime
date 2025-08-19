from datetime import datetime, timezone
from db import db


class ChatSession(db.Model):
    __tablename__ = "chat_session"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(40), default="Chat session", nullable=False)
    last_used = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class ChatTurn(db.Model):
    __tablename__ = "chat_turn"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer, db.ForeignKey("chat_session.id"), index=True, nullable=False
    )
    prompt = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    outputs = db.relationship(
        "LLMOutput",
        backref="turn",
        lazy="selectin",  # efficient eager load
        order_by="LLMOutput.created_at.asc()",  # oldest→newest within a turn
    )


class LLMOutput(db.Model):
    __tablename__ = "llm_output"
    id = db.Column(db.Integer, primary_key=True)
    turn_id = db.Column(
        db.Integer, db.ForeignKey("chat_turn.id"), index=True, nullable=False
    )
    provider = db.Column(db.String(50), nullable=False)
    summarizer_prompt = db.Column(db.Text, nullable=True)  # non-null iff summarizing
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
