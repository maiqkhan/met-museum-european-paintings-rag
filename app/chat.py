import streamlit as st
from openai import OpenAI

from dotenv import load_dotenv

load_dotenv()

client =  OpenAI()

# developer_prompt = """

# """



st.set_page_config(page_title="MET Museum Guide", page_icon="💬")
st.title("Museum Guide")

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {"role": "developer", "content": developer_prompt},
    ]
if "display_messages" not in st.session_state:
    st.session_state.display_messages = []
if "pending_response" not in st.session_state:
    st.session_state.pending_response = False

for msg in st.session_state.display_messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.markdown(msg["content"])
    elif msg["role"] == "function_call":
        with st.chat_message("assistant"):
            with st.expander(f"Function call: {msg['name']}({msg['arguments']})"):
                st.markdown(f"**Call:** `{msg['name']}({msg['arguments']})`")
                st.markdown(f"**Output:**\n```json\n{msg['output']}\n```")

prompt = st.chat_input("Ask a question...")
if prompt:
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    st.session_state.display_messages.append({"role": "user", "content": prompt})
    st.session_state.pending_response = True
    st.rerun()            

if st.session_state.pending_response:
    with tracer.start_as_current_span("assistant-turn", openinference_span_kind="chain") as span:
        try:
            chain_input_question = ""
            chain_output_answer = ""
            while True:
                