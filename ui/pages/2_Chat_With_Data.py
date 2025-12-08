import os
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

st.title("💬 Chat With Your Data")

# ---------------------------------------------------------
# Load uploaded files
# ---------------------------------------------------------
try:
    resp = requests.get(f"{API_BASE}/v1/files")
    files = resp.json().get("data", [])
except Exception as e:
    st.error(f"Unable to load files: {e}")
    st.stop()

if not files:
    st.warning("No uploaded files found.")
    st.stop()

# ---------------------------------------------------------
# File Selector
# ---------------------------------------------------------
file_map = {f"{f['filename']} ({f['id']})": f["id"] for f in files}
selected_label = st.selectbox("Select a file to chat with:", list(file_map.keys()))
file_id = file_map[selected_label]

st.info(f"Chatting with: **{selected_label}**")

# ---------------------------------------------------------
# Chat Input
# ---------------------------------------------------------
query = st.text_input("Ask a question about this file:")

if st.button("Ask AI"):
    if not query.strip():
        st.error("Please enter a question.")
        st.stop()

    with st.spinner("Thinking..."):
        try:
            resp = requests.post(
                f"{API_BASE}/v1/ask/file/{file_id}",
                json={"question": query},
            )
        except Exception as e:
            st.error(f"Request failed: {e}")
            st.stop()

        if not resp.ok:
            st.error(resp.text)
            st.stop()

        data = resp.json().get("data", {})

        # -------------------------
        # Render answer
        # -------------------------
        st.subheader("🧠 Answer")
        st.write(data.get("answer", "No answer returned"))
