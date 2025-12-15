import streamlit as st
import requests
import pandas as pd
import plotly.express as px

API_BASE = st.secrets.get("API_BASE", "http://localhost:8000")

st.title("📊 Dataset Browser")

# ---------------------------------------------------------
# Load uploaded files
# ---------------------------------------------------------
st.sidebar.header("📁 Uploaded Files")

try:
    resp = requests.get(f"{API_BASE}/v1/files")
    st.json(resp.json())
    print("Response", resp.json())
    files = resp.json().get("data", [])
except Exception as e:
    st.error(f"❌ Unable to load files: {e}")
    st.stop()

if not files:
    st.info("No files have been uploaded yet.")
    st.stop()

# ---------------------------------------------------------
# Sidebar Modern Card UI
# ---------------------------------------------------------

# Add CSS for sidebar cards
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
.open-btn {
    background-color: #2563eb;
    color: white;
    padding: 4px 10px;
    border-radius: 6px;
    border: none;
    font-size: 0.75rem;
}
.delete-btn {
    background-color: #ef4444;
    color: white;
    padding: 4px 10px;
    border-radius: 6px;
    border: none;
    font-size: 0.75rem;
}
</style>
""", unsafe_allow_html=True)

# Maintain selected file
if "selected_file_id" not in st.session_state:
    st.session_state["selected_file_id"] = files[0]["id"]

# Sidebar file cards
for f in files:
    with st.sidebar.container():
        st.markdown(f"""
        <div class="sidebar-card">
            <div class="sidebar-title">📄 {f['filename']}</div>
            <div class="sidebar-meta">Type: {f['doc_type']}</div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.sidebar.columns([1, 1])

        if c1.button("Open", key=f"open_{f['id']}"):
            st.session_state["selected_file_id"] = f["id"]
            st.rerun()

        if c2.button("Delete", key=f"delete_{f['id']}"):
            try:
                del_resp = requests.delete(f"{API_BASE}/v1/files/{f['id']}")
                if del_resp.status_code == 200:
                    st.sidebar.success("File deleted")
                    st.rerun()
                else:
                    st.sidebar.error("Delete failed")
            except Exception as e:
                st.sidebar.error(f"Error: {e}")

    st.sidebar.markdown("---")

file_id = st.session_state["selected_file_id"]
selected_file = next((f for f in files if f["id"] == file_id), None)
selected_label = selected_file["filename"] if selected_file else "Selected File"

# ---------------------------------------------------------
# Uploaded document metadata
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
# Load extracted rows
# ---------------------------------------------------------
st.subheader(f"📚 Records for: {selected_label}")

try:
    rows_resp = requests.get(f"{API_BASE}/v1/files/{file_id}/rows").json()
    
    rows = rows_resp.get("data", [])
except Exception as e:
    st.error(f"❌ Unable to fetch rows: {e}")
    st.stop()

# ---------------------------------------------------------
# CASE 1 — NO TABLE ROWS (TEXT DOCUMENT)
# ---------------------------------------------------------
if not rows:
    st.warning("This file does not contain any row data. Showing text & AI analysis options.")

    st.subheader("📘 Extracted Text (Preview)")

    try:
        text_resp = requests.get(f"{API_BASE}/v1/files/{file_id}/text").json()
        raw_text = text_resp.get("data", {}).get("text", "")
    except:
        st.error("Could not extract text.")
        st.stop()

    if not raw_text:
        st.error("No readable text found.")
        st.stop()

    clean_text = raw_text.strip().replace("•", "\n- ").replace("●", "\n- ").replace("▪", "\n- ")
    clean_text = clean_text.replace(". ", ".\n")

    st.markdown(
        f"""
        <div style="
            background-color:#f7f7f7;
            padding: 18px;
            border-radius: 12px;
            max-height: 480px;
            overflow-y: auto;
            white-space: pre-wrap;
            line-height: 1.6;
            font-size: 15px;
        ">
            {clean_text}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.subheader("🤖 AI Summary & Insights")

    if st.button("✨ Generate AI Summary"):
        try:
            ai_resp = requests.post(
                f"{API_BASE}/v1/analysis/llm_summary",
                json={"text": raw_text}
            ).json()

            summary = ai_resp.get("data", None)

            if isinstance(summary, dict):
                summary = summary.get("summary", "No response")

            st.markdown("## 🧠 AI Summary")
            st.write(summary or "No response")
        except Exception as e:
            st.error(f"AI Summary Failed: {e}")

# ---------------------------------------------------------
# CASE 2 — TABLE ROWS
# ---------------------------------------------------------
df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True)

# ---------------------------------------------------------
# Summary stats
# ---------------------------------------------------------
st.header("📈 Summary Statistics")

try:
    summary_resp = requests.get(
        f"{API_BASE}/v1/analysis/summary",
        params={"file_id": file_id}
    ).json()
    st.json(summary_resp.get("data", {}))
except:
    st.warning("Could not load summary statistics.")


# ---------------------------------------------------------
# 🎛 **Improved Filtering UI**
# ---------------------------------------------------------
st.header("🎛 Data Filters")

with st.expander("🔍 Show Filters", expanded=True):

    # Convert numeric-looking text to numbers
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="ignore")

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    text_cols = df.select_dtypes(include="object").columns.tolist()
    date_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()
    bool_cols = df.select_dtypes(include="bool").columns.tolist()

    filter_col = st.selectbox("Select a column to filter", df.columns)

    temp_df = df.copy()

    if filter_col in numeric_cols:
        col_min = temp_df[filter_col].min()
        col_max = temp_df[filter_col].max()

        if pd.isna(col_min) or pd.isna(col_max) or col_min == col_max:
            st.warning(f"Column '{filter_col}' has no numeric range.")
        else:
            min_val, max_val = st.slider(
                f"Range for {filter_col}",
                float(col_min),
                float(col_max),
                (float(col_min), float(col_max))
            )
            temp_df = temp_df[(temp_df[filter_col] >= min_val) & (temp_df[filter_col] <= max_val)]

    elif filter_col in text_cols:
        unique_vals = temp_df[filter_col].dropna().unique()

        if len(unique_vals) <= 25:
            selected_vals = st.multiselect(
                f"Select {filter_col}",
                options=sorted(unique_vals),
                default=sorted(unique_vals)
            )
            temp_df = temp_df[temp_df[filter_col].isin(selected_vals)]
        else:
            keyword = st.text_input(f"Search in {filter_col}")
            case = st.checkbox("Case sensitive?", value=False)
            if keyword:
                temp_df = temp_df[temp_df[filter_col].astype(str).str.contains(keyword, case=case)]

    elif filter_col in date_cols:
        date_min = temp_df[filter_col].min()
        date_max = temp_df[filter_col].max()

        start_date, end_date = st.date_input(
            f"Select date range for {filter_col}",
            value=(date_min, date_max),
        )

        temp_df = temp_df[
            (temp_df[filter_col] >= pd.to_datetime(start_date)) &
            (temp_df[filter_col] <= pd.to_datetime(end_date))
        ]

    elif filter_col in bool_cols:
        choice = st.radio(f"Value for {filter_col}", [True, False, "All"])
        if choice != "All":
            temp_df = temp_df[temp_df[filter_col] == choice]

    if st.button("🔄 Reset Filters"):
        st.rerun()

st.subheader("📄 Filtered Data")
st.dataframe(temp_df, use_container_width=True)

st.download_button(
    "⬇ Download Filtered CSV",
    data=temp_df.to_csv(index=False).encode(),
    file_name="filtered_data.csv",
    mime="text/csv"
)

# ---------------------------------------------------------
# Visualizations
# ---------------------------------------------------------
st.header("📊 Visualizations")

try:
    plots_resp = requests.get(
        f"{API_BASE}/v1/analysis/plots",
        params={"file_id": file_id}
    ).json()
    plots = plots_resp.get("data", {})
except:
    plots = {}
    st.warning("Could not load plots.")

if plots:
    for col, plot_data in plots.items():
        st.subheader(f"Histogram: {col}")
        fig = px.bar(x=plot_data["bins"], y=plot_data["counts"])
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# AI Table Q&A
# ---------------------------------------------------------
st.header("🤖 AI Insights (Table Data)")

question = st.text_input("Ask a question about this dataset")

if st.button("Ask AI") and question.strip():
    try:
        ai_resp = requests.get(
            f"{API_BASE}/v1/analysis/descriptive",
            params={"file_id": file_id, "question": question}
        ).json()
        st.subheader("AI Response")
        st.write(ai_resp.get("data", "No response"))
    except Exception as e:
        st.error(f"AI request failed: {e}")
