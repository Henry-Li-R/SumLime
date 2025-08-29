# tests/test_llm_retry.py
import pytest
import requests
import httpx

from core.providers.base import llm_retry, is_retryable_llm

# OpenAI SDK exception classes (v1)
from openai import APIConnectionError, APITimeoutError, RateLimitError, APIStatusError


RETRYABLE_STATUSES = {408, 429, 500, 502, 503, 504}


class DummyStatusError(APIStatusError):
    """APIStatusError test double backed by an httpx.Response."""

    def __init__(
        self,
        status_code: int,
        message: str = "status error",
        body: bytes | str | dict | None = None,
    ):
        if isinstance(body, (bytes, bytearray)):
            content = body
        elif isinstance(body, str):
            content = body.encode("utf-8")
        elif body is None:
            content = b""
        else:
            content = str(body).encode("utf-8")

        resp = httpx.Response(
            status_code=status_code,
            content=content,
            request=httpx.Request("GET", "https://example.test"),
        )
        super().__init__(message=message, response=resp, body=body)
        # convenience for predicates that read getattr(exc, "status_code", None)
        self.status_code = status_code


# ---------- Unit tests: predicate ----------


@pytest.mark.parametrize(
    "exc",
    [
        requests.Timeout("timeout"),
        requests.ConnectionError("conn error"),
        # OpenAI v1 exception instances with required args
        APIConnectionError(
            message="api conn", request=httpx.Request("GET", "https://example.test")
        ),
        APITimeoutError(httpx.Request("GET", "https://example.test")),
        RateLimitError(
            message="rate limit",
            response=httpx.Response(
                429, request=httpx.Request("GET", "https://example.test")
            ),
            body=None,
        ),
        *[DummyStatusError(s) for s in RETRYABLE_STATUSES],
    ],
)
def test_is_retryable_llm_true(exc):
    assert is_retryable_llm(exc) is True


@pytest.mark.parametrize(
    "exc",
    [
        Exception("generic"),
        RuntimeError("not retryable"),
        DummyStatusError(418),  # not in RETRYABLE_STATUSES
        DummyStatusError(404),  # not in RETRYABLE_STATUSES
    ],
)
def test_is_retryable_llm_false(exc):
    assert is_retryable_llm(exc) is False


# ---------- Integration tests: decorator retries ----------


def _make_api_conn_err():
    return APIConnectionError(
        message="api conn", request=httpx.Request("GET", "https://example.test")
    )


def _make_api_timeout_err():
    return APITimeoutError(request=httpx.Request("GET", "https://example.test"))


def _make_rate_limit_err():
    return RateLimitError(
        message="rate limit",
        response=httpx.Response(
            429, request=httpx.Request("GET", "https://example.test")
        ),
        body=None,
    )


@pytest.mark.parametrize(
    "exc_factory",
    [
        lambda: requests.Timeout("timeout"),
        lambda: requests.ConnectionError("conn error"),
        _make_api_conn_err,
        _make_api_timeout_err,
        _make_rate_limit_err,
        *[lambda s=s: DummyStatusError(s) for s in RETRYABLE_STATUSES],
    ],
)
def test_llm_retry_retries_three_times(exc_factory):
    calls = {"n": 0}

    @llm_retry()  # assumes reraise=True in your decorator
    def flaky():
        calls["n"] += 1
        raise exc_factory()

    with pytest.raises(BaseException):
        flaky()

    assert calls["n"] == 3, f"expected 3 attempts, got {calls['n']}"
