# MathBuddy — NC Math Tutor

An AI-powered math tutor for 5th–6th grade students, aligned to the
North Carolina DPI Mathematics Standard Course of Study.

MathBuddy runs a structured, adaptive tutoring session: it collects the
student's name, target problem count, and chosen NC DPI standard (or a
topic cluster like "Fractions" or "Mix It Up"), then presents problems
one at a time, evaluates answers with encouraging feedback, and delivers
a full performance summary at the end. All session and progress data is
stored locally in a SQLite database.

## Prerequisites

- Python 3.13+
- An OpenAI API key (used for the model and optional content moderation)

## Setup

```bash
git clone https://github.com/<your-username>/nc-math-tutor.git
cd nc-math-tutor
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # then edit .env and add your OPENAI_API_KEY
```

## Run

```bash
python app.py
```

Open your browser at **http://localhost:7860**

## Reset Session History

```bash
rm tutor.db    # deletes all SQLite history — cannot be undone
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | — | OpenAI API key for the model and moderation |
| `MODEL` | No | `gpt-4o` | Model used by the agent |
| `DB_PATH` | No | `tutor.db` | Path to the SQLite database file |
| `OPENAI_AGENTS_TRACE` | No | `0` | Set to `1` to enable OpenAI Agents SDK tracing (dev mode) |

## Testing

```bash
pytest tests/
```

## Documentation

- `getting_started.md` — how to launch the app and 10 sample prompts to try manually.
- `agents.md` — the authoritative design and operating specification.

## Project Structure

```
nc-math-tutor/
├── app.py                     # Gradio chat interface entry point
├── agents/
│   ├── math_tutor.py          # Agent definition, session lifecycle, runner
│   └── session_state.py       # In-memory session state dataclass
├── tools/
│   ├── problem_generator.py   # generate_problem tool
│   ├── answer_evaluator.py    # evaluate_answer tool
│   ├── db_tools.py            # save_session_to_db, get_student_history tools
│   ├── standards_catalog.py   # get_nc_standards tool
│   ├── summarizer.py          # generate_session_summary tool
│   ├── schemas.py             # Pydantic output-schema validation
│   ├── moderation.py          # child-safe content check
│   └── logging_utils.py       # structured JSON-line logging
├── db/
│   ├── database.py            # SQLite connection, schema creation
│   └── schema.sql             # Reference DDL
├── standards/
│   └── nc_standards.py        # NC DPI 5th–6th grade standard definitions
├── prompts/
│   └── system_prompt.txt      # Versioned system prompt
└── tests/
    ├── test_tools.py
    ├── test_agent.py
    ├── test_eval.py
    ├── test_spotcheck.py
    └── eval_cases.json        # Evaluation case suite
```
