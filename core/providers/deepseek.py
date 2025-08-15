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

    def query(self, prompt: str, chat_turn: int, chat_session: int, is_summarizing: bool = False, system_message="") -> str:
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
        
        # Fetch prior turns oldest→newest (optionally cap with a LIMIT/K window)
        prev_turns = (
            ChatTurn.query
            .filter_by(session_id=chat_session)
            .order_by(ChatTurn.created_at.asc())
            .all()[:-1] # newest turn has not been associated with any LLMOutput
        )
                
        for turn in prev_turns:
            if is_summarizing:
                # Prefer the latest summarizer_prompt for this turn; fall back to turn.prompt
                sp_row = (
                    LLMOutput.query
                    .filter(
                        LLMOutput.turn_id == turn.id,
                        LLMOutput.summarizer_prompt.isnot(None)
                    )
                    .order_by(LLMOutput.created_at.desc())
                    .first()
                )
                user_text = sp_row.summarizer_prompt if sp_row and sp_row.summarizer_prompt else turn.prompt

                # The assistant message should be the DeepSeek row produced under summarization
                ds_row = (
                    LLMOutput.query
                    .filter(
                        LLMOutput.turn_id == turn.id,
                        LLMOutput.provider == "deepseek",
                        LLMOutput.summarizer_prompt.isnot(None)
                    )
                    .order_by(LLMOutput.created_at.desc())
                    .first()
                )
            else:
                # Non-summarizing path: canonical prompt + DeepSeek base output (no summarizer_prompt)
                user_text = turn.prompt
                ds_row = (
                    LLMOutput.query
                    .filter(
                        LLMOutput.turn_id == turn.id,
                        LLMOutput.provider == "deepseek",
                        LLMOutput.summarizer_prompt.is_(None)
                    )
                    .order_by(LLMOutput.created_at.desc())
                    .first()
                )

            # Append user turn
            messages.append({"role": "user", "content": user_text})

            # Append assistant turn if present
            if ds_row and ds_row.content:
                messages.append({"role": "assistant", "content": ds_row.content})
        
        # Current user message (caller passes the correct prompt for current mode)
        messages.append({"role": "user", "content": prompt})
        
        # Call DeepSeek
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=False
        )
        text = (response.choices[0].message.content or "").strip()
        
        # Commit new LLMOutput to db
        llm_output = LLMOutput(
            turn_id=chat_turn,
            provider="deepseek",
            summarizer_prompt=prompt if is_summarizing else None,
            content=text,
        )
        db.session.add(llm_output)
        db.session.commit()
        
        '''
        print("\n\n")
        print("deepseek chat history")
        print(messages)
        print("\n\n")
        '''
        
        return text