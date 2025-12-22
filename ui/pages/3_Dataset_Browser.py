import os
import requests
import streamlit as st
import pandas as pd
import plotly.express as px

from auth_guard import require_auth

# ---------------------------------------------------------
# AUTH
# ---------------------------------------------------------
require_auth()

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

headers = {
    "Authorization": f"Bearer {st.session_state['token']}"
}

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.title("📊 Dataset Browser")

# ---------------------------------------------------------
# SIDEBAR: LOGOUT
# ---------------------------------------------------------
with st.sidebar:
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

st.sidebar.header("📁 Uploaded Files")

# ---------------------------------------------------------
# Load uploaded files
# ---------------------------------------------------------
try:
    resp = requests.get(
        f"{API_BASE}/v1/files",
        headers=headers,
        timeout=30
    )

    if resp.status_code == 401:
        st.error("Session expired. Please login again.")
        st.session_state.clear()
        st.rerun()

    files = resp.json().get("data", [])

except Exception as e:
    st.error(f"❌ Unable to load files: {e}")
    st.stop()

if not files:
    st.info("No files have been uploaded yet.")
    st.stop()

# ---------------------------------------------------------
# Sidebar Card Styles
# ---------------------------------------------------------
st.sidebar.markdown("""
<style>
.sidebar-card {
    padding: 10px;
    border-radius: 10px;
    background-color: #f8f9fa;
    margin-bottom: 12px;
    border: 1px solid #e5e7eb;
    transition: all 0.2s ease-in-out;
}
.sidebar-card:hover {
    background-color: #eef2ff;
    transform: translateX(4px);
}
.sidebar-title {
    font-size: 0.90rem;
    font-weight: 600;
    margin-bottom: 4px;
}
.sidebar-meta {
    font-size: 0.75rem;
    color: #6b7280;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Maintain selected file
# ---------------------------------------------------------
if "selected_file_id" not in st.session_state:
    st.session_state["selected_file_id"] = files[0]["id"]

# ---------------------------------------------------------
# Sidebar File Cards
# ---------------------------------------------------------
for f in files:
    with st.sidebar.container():
        st.markdown(
            f"""
            <div class="sidebar-card">
                <div class="sidebar-title">📄 {f['filename']}</div>
                <div class="sidebar-meta">Type: {f.get('doc_type','-')}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        c1, c2 = st.sidebar.columns(2)

        if c1.button("Open", key=f"open_{f['id']}"):
            st.session_state["selected_file_id"] = f["id"]
            st.rerun()

        if c2.button("Delete", key=f"delete_{f['id']}"):
            del_resp = requests.delete(
                f"{API_BASE}/v1/files/{f['id']}",
                headers=headers,
                timeout=30
            )

            if del_resp.status_code == 401:
                st.error("Session expired. Please login again.")
                st.session_state.clear()
                st.rerun()

            if del_resp.ok:
                st.sidebar.success("File deleted")
                st.rerun()
            else:
                st.sidebar.error("Delete failed")

    st.sidebar.markdown("---")

# ---------------------------------------------------------
# Selected File
# ---------------------------------------------------------
file_id = st.session_state["selected_file_id"]
selected_file = next((f for f in files if f["id"] == file_id), None)
selected_label = selected_file["filename"] if selected_file else "Selected File"

# ---------------------------------------------------------
# File Metadata
# ---------------------------------------------------------
st.subheader("📄 Uploaded Documents")

try:
    file_df = pd.DataFrame(files)
    cols = ["id", "filename", "doc_type", "content_type", "created_at"]
    cols = [c for c in cols if c in file_df.columns]
    st.dataframe(file_df[cols], use_container_width=True)
except:
    st.warning("Unable to display file metadata.")

# ---------------------------------------------------------
# Load Extracted Rows
# ---------------------------------------------------------
st.subheader(f"📚 Records for: {selected_label}")

rows_resp = requests.get(
    f"{API_BASE}/v1/files/{file_id}/rows",
    headers=headers,
    timeout=30
).json()

rows = rows_resp.get("data", [])

# ---------------------------------------------------------
# CASE 1 — TEXT DOCUMENT
# ---------------------------------------------------------
if not rows:
    st.warning("This file does not contain table data.")

    st.subheader("📘 Extracted Text")

    text_resp = requests.get(
        f"{API_BASE}/v1/files/{file_id}/text",
        headers=headers,
        timeout=30
    ).json()

    raw_text = text_resp.get("data", {}).get("text", "")

    if not raw_text:
        st.error("No readable text found.")
        st.stop()

    clean_text = (
        raw_text.strip()
        .replace("•", "\n- ")
        .replace("●", "\n- ")
        .replace("▪", "\n- ")
        .replace(". ", ".\n")
    )

    st.markdown(
        f"""
        <div style="
            background:#f7f7f7;
            padding:18px;
            border-radius:12px;
            max-height:480px;
            overflow-y:auto;
            white-space:pre-wrap;
            line-height:1.6;
        ">
        {clean_text}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.subheader("🤖 AI Summary")

    if st.button("✨ Generate AI Summary"):
        ai_resp = requests.post(
            f"{API_BASE}/v1/analysis/llm_summary",
            json={"text": raw_text},
            headers=headers,
            timeout=60
        ).json()

        summary = ai_resp.get("data", {})
        st.write(summary.get("summary", summary))

    st.stop()

# ---------------------------------------------------------
# CASE 2 — TABLE DATA
# ---------------------------------------------------------
df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True)

# ---------------------------------------------------------
# Summary Statistics
# ---------------------------------------------------------
st.header("📈 Summary Statistics")

summary_resp = requests.get(
    f"{API_BASE}/v1/analysis/summary",
    params={"file_id": file_id},
    headers=headers,
    timeout=30
).json()

st.json(summary_resp.get("data", {}))

# ---------------------------------------------------------
# Filters
# ---------------------------------------------------------
st.header("🎛 Data Filters")

with st.expander("🔍 Show Filters", expanded=True):

    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="ignore")

    filter_col = st.selectbox("Select column", df.columns)
    temp_df = df.copy()

    if pd.api.types.is_numeric_dtype(temp_df[filter_col]):
        min_v, max_v = temp_df[filter_col].min(), temp_df[filter_col].max()
        min_val, max_val = st.slider(
            "Range",
            float(min_v),
            float(max_v),
            (float(min_v), float(max_v)),
        )
        temp_df = temp_df[
            (temp_df[filter_col] >= min_val) &
            (temp_df[filter_col] <= max_val)
        ]

    elif pd.api.types.is_object_dtype(temp_df[filter_col]):
        vals = temp_df[filter_col].dropna().unique().tolist()
        selected = st.multiselect("Values", vals, default=vals)
        temp_df = temp_df[temp_df[filter_col].isin(selected)]

    if st.button("Reset Filters"):
        st.rerun()

st.subheader("📄 Filtered Data")
st.dataframe(temp_df, use_container_width=True)

st.download_button(
    "⬇ Download CSV",
    temp_df.to_csv(index=False).encode(),
    file_name="filtered_data.csv",
    mime="text/csv",
)

# ---------------------------------------------------------
# Visualizations
# ---------------------------------------------------------
st.header("📊 Visualizations")

plots_resp = requests.get(
    f"{API_BASE}/v1/analysis/plots",
    params={"file_id": file_id},
    headers=headers,
    timeout=30
).json()

plots = plots_resp.get("data", {})

for col, plot_data in plots.items():
    st.subheader(f"Histogram: {col}")
    fig = px.bar(x=plot_data["bins"], y=plot_data["counts"])
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# AI Table Q&A
# ---------------------------------------------------------
st.header("🤖 AI Insights")

question = st.text_input("Ask a question about this dataset")

if st.button("Ask AI") and question.strip():
    ai_resp = requests.get(
        f"{API_BASE}/v1/analysis/descriptive",
        params={"file_id": file_id, "question": question},
        headers=headers,
        timeout=60
    ).json()

    st.subheader("AI Response")
    st.write(ai_resp.get("data", "No response"))
