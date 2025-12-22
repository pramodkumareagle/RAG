import streamlit as st
import requests
from auth_api import require_auth, auth_headers, logout

API_BASE = "http://localhost:8000"

require_auth()
st.title("💬 Chat With Data")

# ------------------------------------
# SIDEBAR
# ------------------------------------
with st.sidebar:
    st.subheader("🧠 Chats")

    if st.button("+ New Chat"):
        requests.post(
            f"{API_BASE}/v1/chat/sessions",
            params={"chat_type": "rag"},
            headers=auth_headers(),
        )
        st.rerun()

    resp = requests.get(
        f"{API_BASE}/v1/chat/sessions",
        headers=auth_headers(),
    ).json()

    sessions = resp.get("data", [])

    if "active_chat" not in st.session_state:
        st.session_state.active_chat = sessions[0]["id"] if sessions else None

    for s in sessions:
        if st.button(s["title"], key=s["id"]):
            st.session_state.active_chat = s["id"]
            st.rerun()

    st.divider()
    if st.button("🚪 Logout"):
        logout()

# ------------------------------------
# LOAD MESSAGES
# ------------------------------------
messages = []
if st.session_state.active_chat:
    msg_resp = requests.get(
        f"{API_BASE}/v1/chat/sessions/{st.session_state.active_chat}/messages",
        headers=auth_headers(),
    ).json()
    messages = msg_resp.get("data", [])

for m in messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ------------------------------------
# INPUT
# ------------------------------------
prompt = st.chat_input("Ask a question...")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    res = requests.post(
        f"{API_BASE}/v1/ask",
        json={"query": prompt},
        headers=auth_headers(),
    ).json()

    answer = res["data"]["answer"]

    with st.chat_message("assistant"):
        st.markdown(answer)

    st.rerun()
