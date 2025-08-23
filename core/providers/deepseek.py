from core.providers.base import LLMProvider
from openai import OpenAI
import os

from db import db
from core.providers.models import ChatSession, ChatTurn, LLMOutput


class DeepSeekProvider(LLMProvider):

    def __init__(self):
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not set in environment variables")
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    def query(
        self,
        prompt: str,
        chat_turn: int,
        chat_session: int,
        is_summarizing: bool = False,
        system_message="",
    ) -> str:
        """
        Build provider-specific chat history:
          - If is_summarizing: use each turn's summarizer_prompt (if present) as the 'user' text,
            and the DeepSeek output whose summarizer_prompt is NOT NULL as the 'assistant'.
          - Else: use turn.prompt as the 'user' text, and the DeepSeek output with summarizer_prompt IS NULL.
        Falls back safely when rows are missing.
        """
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})

        # 1) Prior turns (oldest→newest), exclude current turn in SQL
        prev_turns = (
            ChatTurn.query
            .filter(ChatTurn.session_id == chat_session,
                    ChatTurn.id != chat_turn)
            .order_by(ChatTurn.created_at.asc(), ChatTurn.id.asc())
            .all()
        )
        
        prev_turn_ids = [t.id for t in prev_turns]
        if not prev_turn_ids:
            prev_turn_ids = [-1]  # keep IN() valid but return 0 rows

        # 2) Fetch the (single) DeepSeek output per turn (no ORDER BY needed)
        outputs_by_turn = {
            o.turn_id: o
            for o in (
                LLMOutput.query
                .filter(LLMOutput.turn_id.in_(prev_turn_ids),
                        LLMOutput.provider == "deepseek")
                .all()
            )
        }

        # 3) Build chat history
        for turn in prev_turns:
            o = outputs_by_turn.get(turn.id)
            if is_summarizing:
                # Prefer summarizer_prompt if present;
                # otherwise fall back to the original prompt
                user_text = o.summarizer_prompt if (o and o.summarizer_prompt) else turn.prompt
            else:
                user_text = turn.prompt

            messages.append({"role": "user", "content": user_text})
            if o and o.content:
                messages.append({"role": "assistant", "content": o.content})

        # Current user message (caller passes the correct prompt for current mode)
        messages.append({"role": "user", "content": prompt})

        # Call DeepSeek
        response = self.client.chat.completions.create(
            model="deepseek-chat", messages=messages, stream=False
        )
        text = (response.choices[0].message.content or "").strip()

        # Sanitize latex
        def sanitize_latex(text: str) -> str:
            text = text.replace("\\(", "$")
            text = text.replace("\\)", "$")
            text = text.replace("\\[", "$$")
            text = text.replace("\\]", "$$")
            return text

        text = sanitize_latex(text)

        # Commit new LLMOutput to db
        llm_output = LLMOutput(
            turn_id=chat_turn,
            provider="deepseek",
            summarizer_prompt=prompt if is_summarizing else None,
            content=text,
        )
        db.session.add(llm_output)
        db.session.commit()

        """
        print("\n\n")
        print("deepseek chat history")
        print(messages)
        print("\n\n")
        """
        return text
