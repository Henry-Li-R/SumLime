from google import genai
from core.providers.base import LLMProvider
import os

from db import db
from core.providers.models import ChatTurn, LLMOutput


class GeminiProvider(LLMProvider):

    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment variables")
        self.client = genai.Client(api_key=api_key)

    def create_chat_title(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=f"Given prompt below, generate descriptive chat title, without quotes, at max 35 chars\n" \
            f"{prompt}",
        )
        text = (response.text or "").strip()
        return text

    def query(
        self,
        prompt: str,
        chat_turn: int,
        chat_session: int,
        is_summarizing: bool = False,
        system_message: str = "",
    ) -> str:
        """
        Build provider-specific chat history for Gemini:
          - If is_summarizing: use each turn's summarizer_prompt (if present) as the 'user' text,
            and the Gemini output whose summarizer_prompt is NOT NULL as the 'model'.
          - Else: use turn.prompt as the 'user' text, and the Gemini output with summarizer_prompt IS NULL.
        Falls back safely when rows are missing.
        """
        # Gemini expects "contents" with roles ('user'/'model') and "parts":[{"text": "..."}]
        contents = []
        if system_message:
            contents.append(
                {
                    "role": "user",  # Gemini uses 'user' for system-like priming in this setup
                    "parts": [{"text": system_message}],
                }
            )

        # Fetch prior turns oldest→newest
        prev_turns = (
            ChatTurn.query.filter_by(session_id=chat_session)
            .order_by(ChatTurn.created_at.asc())
            .all()[:-1]  # newest turn has not been associated with any LLMOutput
        )

        for turn in prev_turns:
            if is_summarizing:
                # Prefer latest summarizer_prompt for this turn; fallback to turn.prompt
                sp_row = (
                    LLMOutput.query.filter(
                        LLMOutput.turn_id == turn.id,
                        LLMOutput.summarizer_prompt.isnot(None),
                        LLMOutput.provider == "gemini",
                    )
                    .order_by(LLMOutput.created_at.desc())
                    .first()
                )
                user_text = (
                    sp_row.summarizer_prompt
                    if sp_row and sp_row.summarizer_prompt
                    else turn.prompt
                )

                gm_row = sp_row  # already filtered to provider="gemini" and summarizer_prompt not null
                if not gm_row:
                    gm_row = (
                        LLMOutput.query.filter(
                            LLMOutput.turn_id == turn.id,
                            LLMOutput.provider == "gemini",
                            LLMOutput.summarizer_prompt.isnot(None),
                        )
                        .order_by(LLMOutput.created_at.desc())
                        .first()
                    )
            else:
                user_text = turn.prompt
                gm_row = (
                    LLMOutput.query.filter(
                        LLMOutput.turn_id == turn.id,
                        LLMOutput.provider == "gemini",
                        LLMOutput.summarizer_prompt.is_(None),
                    )
                    .order_by(LLMOutput.created_at.desc())
                    .first()
                )

            # Append user part
            contents.append({"role": "user", "parts": [{"text": user_text}]})

            # Append model part if present
            if gm_row and gm_row.content:
                contents.append({"role": "model", "parts": [{"text": gm_row.content}]})

        # Current user message
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        # Call Gemini
        response = self.client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=contents,
        )
        text = (response.text or "").strip()

        # Persist output (provider='gemini'; summarizer_prompt only when summarizing)
        llm_output = LLMOutput(
            turn_id=chat_turn,
            provider="gemini",
            summarizer_prompt=prompt if is_summarizing else None,
            content=text,
        )
        db.session.add(llm_output)
        db.session.commit()

        """
        print("\n\n")
        print("gemini chat history")
        print(contents)
        print("\n\n")
        """

        return text
