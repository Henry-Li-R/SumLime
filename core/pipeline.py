from core.providers.deepseek import DeepSeekProvider

# from core.providers.chatgpt import ChatGPTProvider
# from core.providers.claude import ClaudeProvider
from core.providers.gemini import GeminiProvider

from db import db
from core.providers.models import ChatSession, ChatTurn, User
from datetime import datetime, timezone

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
        
        dummy_user = User.query.filter_by(username="dummy").first()
        if not dummy_user:
            dummy_user = User(username="dummy", email="dummy@example.com")
            db.session.add(dummy_user)
            db.session.commit()

        new_session = ChatSession(title=chat_title, user_id=dummy_user.id)  # type: ignore
        db.session.add(new_session)
        db.session.commit()
        chat_session = new_session.id

    # Update last_used time for current chat_session
    session = ChatSession.query.get_or_404(chat_session)
    session.last_used = datetime.now(timezone.utc)
    db.session.commit()


    # Create new ChatTurn
    new_turn = ChatTurn(
        session_id=chat_session, # type: ignore
        prompt=prompt, # type: ignore
    )
    db.session.add(new_turn)
    db.session.flush()  # ensure new_turn.id is populated before using it

    results = {}
    for model in models:
        results[model] = MODEL_PROVIDERS[model].query(prompt, new_turn.id, chat_session)

    summary_input = "\n\n".join(
        [
            f"{('LLM ' + str(i)) if llm_anonymous else model.upper()}:\n{results[model]}"
            for i, model in enumerate(models, start=1)
            if model in results
        ]
    )

    summary_prompt = f"""Compare and summarize the content of the following responses to the same prompt. Begin by answering the user’s question based on the combined insights. Then analyze similarities and differences in reasoning, and note any ambiguities or missing details.

Prompt:\n\n
{prompt}\n\n
LLM responses:\n\n
{summary_input}
"""
    summary = MODEL_PROVIDERS[summary_model].query(
        summary_prompt, new_turn.id, chat_session, is_summarizing=True
    )
    results["summary"] = summary

    return {
        "prompt": prompt,
        "results": results,
        "session_id": chat_session,
        "turn_id": new_turn.id,
        "created_at": new_turn.created_at.isoformat(),
    }
