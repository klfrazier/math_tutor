from pathlib import Path

from _sdk import Agent

SYSTEM_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "system_prompt.txt"
SYSTEM_PROMPT_TEMPLATE = SYSTEM_PROMPT_PATH.read_text()

math_tutor_agent = Agent(
    name="math-tutor",
    instructions=SYSTEM_PROMPT_TEMPLATE,
)
