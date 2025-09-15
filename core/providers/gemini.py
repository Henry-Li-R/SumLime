from google import genai
from core.providers.base import LLMProvider, llm_retry
import os

from db import db
from core.providers.models import ChatTurn, LLMOutput


class GeminiProvider(LLMProvider):

    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment variables")
        self.client = genai.Client(api_key=api_key)

    @llm_retry()
    def _generate(self, *, contents: list[dict] | str, stream: bool = False):
        """Wrapper around the Gemini client with optional SSE streaming."""
        if stream:
            return self.client.models.generate_content_stream(
                model="gemini-2.0-flash-lite",
                contents=contents,  # type: ignore
            )
        return self.client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=contents,  # type: ignore
        )

    def create_chat_title(self, prompt: str) -> str:
        response = self._generate(
            contents=f"Given prompt below, generate exactly one descriptive chat title, in a ready-to-use format without quotes, at max 35 chars\n{prompt}",
        )
        text = getattr(response, "text", "Chat Session")
        return text.strip()[:40]

    def query(
        self,
        prompt: str,
        chat_turn: int,
        chat_session: int,
        is_summarizing: bool = False,
        system_message: str = "",
    ):
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

        # 1) Prior turns (oldest→newest), exclude current turn in SQL
        prev_turns = (
            db.session.execute(
                db.select(ChatTurn)
                .filter(ChatTurn.session_id == chat_session, ChatTurn.id != chat_turn)
                .order_by(ChatTurn.created_at.asc(), ChatTurn.id.asc())
            )
            .scalars()
            .all()
        )
        prev_turn_ids = [t.id for t in prev_turns]
        if not prev_turn_ids:
            prev_turn_ids = [-1]  # keep IN() valid but return 0 rows

        # 2) Fetch the (single) gemini output per turn (no ORDER BY needed)
        outputs_by_turn = {
            o.turn_id: o
            for o in db.session.execute(
                db.select(LLMOutput).filter(
                    LLMOutput.turn_id.in_(prev_turn_ids),
                    LLMOutput.provider == "gemini",
                )
            )
            .scalars()
            .all()
        }

        # 3) Build chat history
        for turn in prev_turns:
            o = outputs_by_turn.get(turn.id)
            if is_summarizing:
                # Prefer summarizer_prompt if present;
                # otherwise fall back to the original prompt
                user_text = (
                    o.summarizer_prompt if (o and o.summarizer_prompt) else turn.prompt
                )
            else:
                user_text = turn.prompt

            contents.append({"role": "user", "parts": [{"text": user_text}]})
            if o and o.content:
                contents.append({"role": "model", "parts": [{"text": o.content}]})

        # Current user message
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        # Call Gemini using SSE streaming
        stream = self._generate(contents=contents, stream=True)
        text_parts: list[str] = []
        prev_text = ""
        for chunk in stream:
            # Gemini returns the cumulative text so far for each chunk.
            # Emit only the new portion to avoid stammering / repeated output.
            chunk_text = getattr(chunk, "text", "") or ""
            if not chunk_text:
                continue
            new_text = chunk_text[len(prev_text) :]
            prev_text = chunk_text
            if new_text:
                text_parts.append(new_text)
                yield new_text

        text = "".join(text_parts).strip()

        # Persist output (provider='gemini'; summarizer_prompt only when summarizing)
        llm_output = LLMOutput(
            turn_id=chat_turn,  # type: ignore
            provider="gemini",  # type: ignore
            summarizer_prompt=prompt if is_summarizing else None,  # type: ignore
            content=text,  # type: ignore
        )
        db.session.add(llm_output)
        db.session.commit()

        """
        print("\n\n")
        print("gemini chat history")
        print(contents)
        print("\n\n")
        """
