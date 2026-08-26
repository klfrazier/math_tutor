"""Thin re-export of the openai-agents SDK symbols.

The SDK is loaded and bound to ``sys.modules["agents"]`` by the local
``agents/__init__.py`` (which resolves the name collision with this
project's own ``agents/`` package). Tools and the agent import from here
so they never have to reason about that collision themselves.
"""

from agents import Agent, Runner, function_tool  # noqa: F401
