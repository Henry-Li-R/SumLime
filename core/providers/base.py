from abc import ABC, abstractmethod

# --- Retry utility imports for LLM APIs ---
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception,
)
from openai import APIStatusError, APIConnectionError, RateLimitError, APITimeoutError
import requests


class LLMProvider(ABC):

    # SUMMARIZE_MESSAGE = "Compare and summarize the following outputs by different LLMs."
    # "You are a fact-checking assistant. Reply with 'Supported', 'Not Supported', or 'Uncertain', followed by a short explanation on a new line."

    @abstractmethod
    def query(
        self,
        prompt: str,
        chat_turn: int,
        chat_session: int,
        is_summarizing: bool = False,
        system_message="",
    ) -> str:
        pass


# --- Shared retry policy for LLM API clients ---

_RETRYABLE_HTTP = {408, 429, 500, 502, 503, 504}


def is_retryable_llm(exc: BaseException) -> bool:
    """Classify transient errors for LLM providers (OpenAI-compatible or raw HTTP)."""
    # Raw HTTP clients
    if isinstance(exc, (requests.Timeout, requests.ConnectionError)):
        return True
    # OpenAI-compatible SDK
    if isinstance(exc, (APIConnectionError, APITimeoutError)):
        return True
    if isinstance(exc, RateLimitError):
        return True
    if isinstance(exc, APIStatusError):
        status = getattr(exc, "status_code", None)
        return status in _RETRYABLE_HTTP
    return False


def llm_retry(max_attempts: int = 3, initial: float = 0.5, max_wait: float = 2.5):
    """Decorator factory for a standard retry policy across LLM providers."""
    return retry(
        retry=retry_if_exception(is_retryable_llm),
        wait=wait_exponential_jitter(initial=initial, max=max_wait),
        stop=stop_after_attempt(max_attempts),
        reraise=True,
    )
