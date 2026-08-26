from pathlib import Path

from _sdk import Agent

from tools.problem_generator import generate_problem
from tools.answer_evaluator import evaluate_answer
from tools.standards_catalog import get_nc_standards
from tools.summarizer import generate_session_summary

SYSTEM_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "system_prompt.txt"
SYSTEM_PROMPT_TEMPLATE = SYSTEM_PROMPT_PATH.read_text()

math_tutor_agent = Agent(
    name="math-tutor",
    instructions=SYSTEM_PROMPT_TEMPLATE,
    tools=[
        generate_problem,
        evaluate_answer,
        get_nc_standards,
        generate_session_summary,
    ],
)
