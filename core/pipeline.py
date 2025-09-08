from core.providers.deepseek import DeepSeekProvider

# from core.providers.chatgpt import ChatGPTProvider
# from core.providers.claude import ClaudeProvider
from core.providers.gemini import GeminiProvider

from db import db
from core.providers.models import ChatSession, ChatTurn
from datetime import datetime, timezone
from flask import g, abort

MODEL_PROVIDERS = {
    "deepseek": DeepSeekProvider(),
    # "chatgpt": ChatGPTProvider(),
    # "claude": ClaudeProvider(),
    "gemini": GeminiProvider(),
}


def summarize(
    prompt: str,
    models: list[str],
    chat_session: int | None = None,
    summary_model: str = "gemini",
    title_model: str = "gemini",
    llm_anonymous: bool = True,
) -> dict:

    if chat_session is None:  # Create new chat if needed
        chat_title = MODEL_PROVIDERS[title_model].create_chat_title(prompt)
        new_session = ChatSession(title=chat_title, user_id=g.user_id)  # type: ignore
        db.session.add(new_session)
        db.session.commit()
        chat_session = new_session.id

    # Update last_used time for current chat_session
    session = db.session.get(ChatSession, chat_session)
    if session is None:
        abort(404)
    session.last_used = datetime.now(timezone.utc)
    db.session.commit()

    # Create new ChatTurn
    new_turn = ChatTurn(
        session_id=chat_session,  # type: ignore
        prompt=prompt,  # type: ignore
    )
    db.session.add(new_turn)
    db.session.flush()  # ensure new_turn.id is populated before using it

    results: dict[str, str] = {}
    for model in models:
        stream = MODEL_PROVIDERS[model].query(prompt, new_turn.id, chat_session)
        parts: list[str] = []
        for chunk in stream:
            parts.append(chunk)
        results[model] = "".join(parts)

    summary_input = "\n\n".join(
        [
            f"{('LLM ' + str(i)) if llm_anonymous else model.upper()}:\n{results[model]}"
            for i, model in enumerate(models, start=1)
            if model in results
        ]
    )

    "Compare the following responses. First, give a combined answer. Then, list key differences and ambiguities. Keep it brief."
    summary_prompt = f"""Give one concise answer to the original prompt, integrating the best LLM insights.

Prompt:\n\n
{prompt}\n\n
LLM responses:\n\n
{summary_input}
"""
    summary_stream = MODEL_PROVIDERS[summary_model].query(
        summary_prompt, new_turn.id, chat_session, is_summarizing=True
    )
    summary_parts: list[str] = []
    for chunk in summary_stream:
        summary_parts.append(chunk)
    summary = "".join(summary_parts)
    results["summarizer"] = summary

    return {
        "prompt": prompt,
        "results": results,
        "session_id": chat_session,
        "turn_id": new_turn.id,
        "created_at": new_turn.created_at.isoformat(),
    }
