"""Thin re-export of the openai-agents SDK symbols.

The SDK is loaded and bound to ``sys.modules["agents"]`` by the local
``agents/__init__.py`` (which resolves the name collision with this
project's own ``agents/`` package). Tools and the agent import from here
so they never have to reason about that collision themselves.

Tracing is enabled in development when ``OPENAI_AGENTS_TRACE=1`` (the SDK
v0.22.0 does not read this env var itself, so we wire it up here).
"""

import os

from agents import Agent, Runner, function_tool  # noqa: F401
from agents import set_tracing_disabled, set_tracing_export_api_key  # noqa: F401

if os.environ.get("OPENAI_AGENTS_TRACE", "0") == "1":
    set_tracing_disabled(False)
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        set_tracing_export_api_key(api_key)
else:
    set_tracing_disabled(True)
