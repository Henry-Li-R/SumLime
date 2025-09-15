import os
import pytest
from flask import Flask, g
from uuid import uuid4
from typing import Iterator

# Provide dummy API keys so provider modules can be imported without error
os.environ.setdefault("DEEPSEEK_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")

from core.pipeline import summarize, MODEL_PROVIDERS
from core.providers.base import LLMProvider
from core.providers.models import ChatSession, LLMOutput
from db import db


class DummyProvider(LLMProvider):
    """Simple provider that yields preset chunks and persists them."""

    def __init__(self, name: str, chunks: list[str]):
        self.name = name
        self.chunks = chunks

    def query(
        self,
        prompt: str,
        chat_turn: int,
        chat_session: int,
        is_summarizing: bool = False,
        system_message: str = "",
    ) -> Iterator[str]:
        parts: list[str] = []
        for c in self.chunks:
            parts.append(c)
            yield c
        out = LLMOutput(
            turn_id=chat_turn,
            provider=self.name,
            summarizer_prompt=prompt if is_summarizing else None,
            content="".join(parts),
        )
        db.session.add(out)
        db.session.commit()


@pytest.fixture()
def app_ctx():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()
        g.user_id = uuid4()
        yield
        db.drop_all()


def test_summarize_yields_chunks_incrementally(app_ctx):
    session = ChatSession(title="chat", user_id=g.user_id)  # type: ignore[arg-type]
    db.session.add(session)
    db.session.commit()

    orig = MODEL_PROVIDERS.copy()
    MODEL_PROVIDERS.clear()
    MODEL_PROVIDERS.update(
        {
            "dummy": DummyProvider("dummy", ["a", "b"]),
            "summary": DummyProvider("summary", ["x", "y"]),
        }
    )

    try:
        gen = summarize(
            "hello",
            ["dummy"],
            chat_session=session.id,
            summary_model="summary",
            title_model="summary",
        )
        chunks: list[dict] = []
        while True:
            try:
                chunks.append(next(gen))
            except StopIteration as stop:
                final = stop.value
                break

        # provider chunks arrive before summarizer chunks
        assert chunks == [
            {"provider": "dummy", "chunk": "a"},
            {"provider": "dummy", "chunk": "b"},
            {"provider": "summarizer", "chunk": "x"},
            {"provider": "summarizer", "chunk": "y"},
        ]

        assert final["results"]["dummy"] == "ab"
        assert final["results"]["summarizer"] == "xy"

        outputs = db.session.execute(db.select(LLMOutput)).scalars().all()
        assert {o.provider for o in outputs} == {"dummy", "summary"}
        assert any(o.summarizer_prompt is not None for o in outputs)
    finally:
        MODEL_PROVIDERS.clear()
        MODEL_PROVIDERS.update(orig)

