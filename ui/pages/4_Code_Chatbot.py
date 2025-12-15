import streamlit as st
import requests

API_URL = "http://localhost:8000/v1/code-snippet-chat"

st.set_page_config(page_title="Code Chatbot", layout="wide")

st.title("💻 GitHub Code Snippet Chatbot")
st.caption("Ask questions and get real code snippets from public GitHub repositories")

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
question = st.chat_input("Ask for a code snippet...")

if question:
    # Show user message
    st.session_state.messages.append(
        {"role": "user", "content": question}
    )
    with st.chat_message("user"):
        st.markdown(question)

    # Call backend
    with st.chat_message("assistant"):
        with st.spinner("Searching GitHub code..."):
            try:
                res = requests.post(
                    API_URL,
                    json={"question": question},
                    timeout=120
                )
                data = res.json()
                answer = data.get("answer", "No response")

            except Exception as e:
                answer = f"❌ Error: {e}"

            st.markdown(answer)

    # Save assistant message
    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )
