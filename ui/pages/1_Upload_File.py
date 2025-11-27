import os
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

st.title("📤 Upload a File")

uploaded_file = st.file_uploader(
    "Choose a file",
    type=["xlsx", "xls", "csv", "pdf", "docx", "txt"]
)

if uploaded_file:
    st.info(f"Selected: **{uploaded_file.name}**")

if st.button("Upload"):
    if not uploaded_file:
        st.error("Please select a file.")
    else:
        with st.spinner("Uploading..."):
            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type
                )
            }

            resp = requests.post(f"{API_BASE}/v1/upload", files=files)

            if resp.ok:
                st.success("File uploaded successfully! 🎉")
                st.json(resp.json())
            else:
                st.error(resp.text)
