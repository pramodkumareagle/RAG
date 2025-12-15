import streamlit as st
import requests

# -----------------------------
# CONFIG
# -----------------------------
API_URL = "http://localhost:8000/v1/code-snippet-chat"

st.set_page_config(
    page_title="GitHub Code Chatbot",
    layout="wide",
)

# -----------------------------
# UI HEADER
# -----------------------------
st.title("💻 GitHub Code Snippet Chatbot")
st.caption(
    "Searches **public GitHub repositories in real time** and returns real code snippets."
)

# -----------------------------
# SESSION STATE
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------------
# CLEAR CHAT
# -----------------------------
col1, col2 = st.columns([1, 6])
with col1:
    if st.button("🧹 Clear chat"):
        st.session_state.messages = []
        st.rerun()

# -----------------------------
# DISPLAY CHAT HISTORY
# -----------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Show GitHub sources if present
        if msg.get("sources"):
            with st.expander("🔎 GitHub sources"):
                for src in msg["sources"]:
                    st.markdown(
                        f"- **{src['repo']}** → `{src['file']}`  \n"
                        f"  🔗 {src['url']}"
                    )

# -----------------------------
# USER INPUT
# -----------------------------
question = st.chat_input("Ask for a code snippet from GitHub...")

if question:
    # ---- show user message
    st.session_state.messages.append(
        {"role": "user", "content": question}
    )
    with st.chat_message("user"):
        st.markdown(question)

    # ---- call backend
    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching GitHub in real time..."):
            try:
                response = requests.post(
                    API_URL,
                    json={"question": question},
                    timeout=60,
                )
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

    # ---- save assistant message
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "sources": sources,
        }
    )
