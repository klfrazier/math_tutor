import gradio as gr

from agents.math_tutor import run_tutor_turn
from agents.session_state import SessionState
from db.database import init_db

MAX_MESSAGE_LENGTH = 500


def chat_fn(message: str, history: list, state: SessionState):
    message = message or ""
    truncated = False
    if len(message) > MAX_MESSAGE_LENGTH:
        message = message[:MAX_MESSAGE_LENGTH]
        truncated = True
    response, updated_state = run_tutor_turn(message, history, state)
    if truncated:
        response = (
            "*(Your message was longer than 500 characters, so I only read the "
            "first part.)*\n\n" + response
        )
    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": response},
    ]
    return history, updated_state


def start_over():
    return [], "", SessionState()


with gr.Blocks(title="MathBuddy — NC Math Tutor") as demo:
    gr.Markdown("# 🧮 MathBuddy\n*Your NC Math Tutor*")
    state = gr.State(SessionState())
    chatbot = gr.Chatbot(label="MathBuddy", height=500)
    msg = gr.Textbox(
        placeholder="Type your answer or question here...",
        label="Your message",
        autofocus=True,
    )
    with gr.Row():
        submit_btn = gr.Button("Send ➤", variant="primary")
        clear_btn = gr.Button("Start Over 🔄")

    submit_btn.click(chat_fn, [msg, chatbot, state], [chatbot, state])
    msg.submit(chat_fn, [msg, chatbot, state], [chatbot, state])
    clear_btn.click(start_over, None, [chatbot, msg, state])


if __name__ == "__main__":
    init_db()
    demo.launch(share=False)
