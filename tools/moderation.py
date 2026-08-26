"""Child-safe content check for generated problems.

Uses the OpenAI moderation API to flag inappropriate content. Fails open
(returns False) when no API key is configured or the API call errors, so
the deterministic, template-based problem generator is never blocked by a
transient network issue. The templates themselves never produce violent,
adult, or inappropriate content.
"""

import os

from openai import OpenAI

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def check_moderation(text: str) -> bool:
    """Return True if the text is flagged as inappropriate, else False."""
    if not os.environ.get("OPENAI_API_KEY"):
        return False
    try:
        response = _get_client().moderations.create(input=text)
        return bool(response.results[0].flagged)
    except Exception:
        return False
