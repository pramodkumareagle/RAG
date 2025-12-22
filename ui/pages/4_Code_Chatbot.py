import streamlit as st
import requests
import os

from auth_guard import require_auth

# ---------------------------------------------------------
# AUTH
# ---------------------------------------------------------
require_auth()

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
API_URL = f"{API_BASE}/v1/code-snippet-chat"

st.set_page_config(
    page_title="GitHub Code Chatbot",
    layout="wide",
)

headers = {
    "Authorization": f"Bearer {st.session_state['token']}"
}

# ---------------------------------------------------------
# SIDEBAR: LOGOUT
# ---------------------------------------------------------
with st.sidebar:
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# ---------------------------------------------------------
# UI HEADER
# ---------------------------------------------------------
st.title("💻 GitHub Code Snippet Chatbot")
st.caption(
    "Searches **public GitHub repositories in real time** and returns real code snippets."
)

# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------------
# CLEAR CHAT
# ---------------------------------------------------------
col1, col2 = st.columns([1, 6])
with col1:
    if st.button("🧹 Clear chat"):
        st.session_state.messages = []
        st.rerun()

# ---------------------------------------------------------
# DISPLAY CHAT HISTORY
# ---------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg.get("sources"):
            with st.expander("🔎 GitHub sources"):
                for src in msg["sources"]:
                    st.markdown(
                        f"- **{src['repo']}** → `{src['file']}`  \n"
                        f"  🔗 {src['url']}"
                    )

# ---------------------------------------------------------
# USER INPUT
# ---------------------------------------------------------
question = st.chat_input("Ask for a code snippet from GitHub...")

if question:
    # -------------------------
    # Show user message
    # -------------------------
    st.session_state.messages.append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user"):
        st.markdown(question)

    # -------------------------
    # Call backend
    # -------------------------
    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching GitHub in real time..."):
            try:
                response = requests.post(
                    API_URL,
                    json={"question": question},
                    headers=headers,
                    timeout=60,
                )

                if response.status_code == 401:
                    st.error("Session expired. Please login again.")
                    st.session_state.clear()
                    st.rerun()

                response.raise_for_status()
                data = response.json()

                answer = data.get("answer", "No response")
                sources = data.get("sources", [])

                st.markdown(answer)

                if sources:
                    with st.expander("🔎 GitHub sources"):
                        for src in sources:
                            st.markdown(
                                f"- **{src['repo']}** → `{src['file']}`  \n"
                                f"  🔗 {src['url']}"
                            )

            except Exception as e:
                answer = f"❌ Error contacting backend: {e}"
                sources = []
                st.error(answer)

    # -------------------------
    # Save assistant message
    # -------------------------
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "sources": sources,
        }
    )
