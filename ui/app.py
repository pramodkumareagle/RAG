import os
import streamlit as st

# Streamlit page config
st.set_page_config(
    page_title="Enterprise RAG UI",
    page_icon="🤖",
    layout="wide"
)

# Read API_BASE from environment
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

# Main landing page
st.title("🤖 Enterprise RAG – Demo UI")
st.write("Welcome! Use the left sidebar to navigate:")

st.markdown("""
### 📤 Upload File
Upload Excel/CSV/PDF/DOCX/TXT files.  
The backend will parse tables and store them in PostgreSQL.

### 💬 Chat with Data
Ask structured questions (counts, lists, filters) or natural questions.  
The backend will use **SQL for structured questions** and **RAG for text-based questions**.
""")

# Show API status
st.subheader("API Status")

import requests

try:
    resp = requests.get(f"{API_BASE}/health")
    if resp.ok:
        st.success("Backend API is reachable 🎉")
    else:
        st.error(f"API responded with status: {resp.status_code}")
except Exception as e:
    st.error(f"Cannot reach API: {e}")
