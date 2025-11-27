import os
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

st.title("💬 Chat With Your Data")

query = st.text_input("Ask a question about your uploaded dataset:")
top_k = st.number_input("Top K", 1, 20, 6)

if st.button("Ask"):
    with st.spinner("Thinking..."):
        try:
            resp = requests.post(
                f"{API_BASE}/v1/ask",
                json={"query": query, "top_k": top_k},
            )
        except Exception as e:
            st.error(e)
            st.stop()

        if not resp.ok:
            st.error(resp.text)
            st.stop()

        data = resp.json().get("data", {})

        st.subheader("Answer")
        st.write(data.get("answer"))

        citations = data.get("citations", [])
        if citations:
            st.subheader("Citations")
            st.json(citations)
