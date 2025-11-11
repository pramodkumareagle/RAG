import os
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.set_page_config(page_title="Enterprise RAG", layout="wide")
st.title("Enterprise RAG – Demo UI")

query = st.text_input("Ask a question", "What does this system do?")

if st.button("Ask"):
    try:
        resp = requests.post(f"{API_BASE}/v1/ask", json={"query": query})
        if resp.ok:
            data = resp.json()
            st.subheader("Answer")
            st.write(data.get("answer", "No answer"))
            st.subheader("Citations")
            for c in data.get("citations", []):
                st.write(f"doc:{c['doc_id']}#{c['chunk']} (score {c['score']:.3f})")
        else:
            st.error(f"API error: {resp.text}")
    except Exception as e:
        st.error(str(e))
