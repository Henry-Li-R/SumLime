from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func
from db import db

class Profile(db.Model):
    __tablename__ = "profiles"
    id = db.Column(UUID(as_uuid=True), primary_key=True)  # == auth.users.id
    username = db.Column(db.String, unique=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    chat_sessions = db.relationship(
        "ChatSession",
        back_populates="profile",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

class ChatSession(db.Model):
    __tablename__ = "chat_session"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(40), default="Chat session", nullable=False)
    last_used = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    turns = db.relationship(
        "ChatTurn",
        back_populates="chat_session",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="ChatTurn.created_at.asc()",
    )
    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    profile = db.relationship("Profile", back_populates="chat_sessions")
    __table_args__ = (
        db.Index("ix_chat_session_user_lastused", "user_id", "last_used"),
    )

class ChatTurn(db.Model):
    __tablename__ = "chat_turn"
    id = db.Column(db.Integer, primary_key=True)
    prompt = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    session_id = db.Column(
        db.Integer, db.ForeignKey("chat_session.id", ondelete="CASCADE"), nullable=False
    )
    chat_session = db.relationship("ChatSession", back_populates="turns")
    outputs = db.relationship(
        "LLMOutput",
        back_populates="turn",
        lazy="selectin",  # efficient eager load
        cascade="all, delete-orphan",
        order_by="LLMOutput.created_at.asc()",  # oldest→newest within a turn
    )

    __table_args__ = (
        db.Index("ix_chat_turn_session_created", "session_id", "created_at"),
    )


class LLMOutput(db.Model):
    __tablename__ = "llm_output"
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), nullable=False)
    summarizer_prompt = db.Column(db.Text, nullable=True)  # non-null iff summarizing
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    turn_id = db.Column(
        db.Integer, db.ForeignKey("chat_turn.id", ondelete="CASCADE"), nullable=False
    )
    turn = db.relationship("ChatTurn", back_populates="outputs")

    __table_args__ = (
        db.Index("ix_llm_output_turn_created", "turn_id", "created_at"),
    )
