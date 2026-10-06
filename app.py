import os

import streamlit as st
import tiktoken
from openai import OpenAI

from db import create_messages_table, save_message


# -------------------------
# OpenAI configuration
# -------------------------

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

MODEL = "gpt-4.1-nano-2025-04-14"
TEMPERATURE = 0.7
MAX_TOKENS = 100
TOKEN_BUDGET = 1000

SYSTEM_PROMPT = """
You are an angry and sassy assistant.
"""


# -------------------------
# Database setup
# -------------------------

create_messages_table()


# -------------------------
# Tokenizer
# -------------------------

def get_encoding(model):
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        print(
            f"Warning: Tokenizer for model '{model}' not found. "
            "Falling back to 'cl100k_base'."
        )
        return tiktoken.get_encoding("cl100k_base")


ENCODING = get_encoding(MODEL)


def count_tokens(text):
    return len(ENCODING.encode(text))


def total_tokens_used(messages):
    try:
        return sum(count_tokens(msg["content"]) for msg in messages)
    except Exception as e:
        print(f"[token count error]: {e}")
        return 0


def enforce_token_budget(messages, budget=TOKEN_BUDGET):
    try:
        while total_tokens_used(messages) > budget:
            if len(messages) <= 2:
                break
            messages.pop(1)
    except Exception as e:
        print(f"[token budget error]: {e}")


# -------------------------
# Streamlit page
# -------------------------

st.title("Med's Chatbot 🤖")


# -------------------------
# Conversation memory
# -------------------------

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]


# -------------------------
# Display previous messages
# -------------------------

for message in st.session_state.messages:
    if message["role"] == "system":
        continue

    with st.chat_message(message["role"]):
        st.write(message["content"])


# -------------------------
# User input
# -------------------------

user_input = st.chat_input("Type your message...")

if user_input:
    # Save user message in the Streamlit session
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    with st.chat_message("user"):
        st.write(user_input)

    # Save user message in PostgreSQL
    save_message("user", user_input)

    # -------------------------
    # OpenAI API call
    # -------------------------

    response = client.chat.completions.create(
        model=MODEL,
        messages=st.session_state.messages,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )

    reply = response.choices[0].message.content

    # Save assistant response in the Streamlit session
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": reply,
        }
    )

    # Save assistant response in PostgreSQL
    save_message("assistant", reply)

    enforce_token_budget(st.session_state.messages)

    with st.chat_message("assistant"):
        st.write(reply)


# -------------------------
# Token counter
# -------------------------

st.sidebar.write(
    "Current tokens:",
    total_tokens_used(st.session_state.messages),
)


# -------------------------
# Clear chat button
# -------------------------

if st.sidebar.button("Clear chat"):
    st.session_state.messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]
    st.rerun()
