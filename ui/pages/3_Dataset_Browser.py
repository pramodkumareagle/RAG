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
    files = resp.json().get("data", [])
except Exception as e:
    st.error(f"❌ Unable to load files: {e}")
    st.stop()

if not files:
    st.info("No files have been uploaded yet.")
    st.stop()

# ---------------------------------------------------------
# Show uploaded files in main area
# ---------------------------------------------------------
st.subheader("📄 Uploaded Documents")

try:
    file_df = pd.DataFrame(files)

    # Only show useful columns
    columns_to_show = [
        col for col in ["id", "filename", "doc_type", "content_type", "created_at"]
        if col in file_df.columns
    ]

    st.dataframe(
        file_df[columns_to_show],
        use_container_width=True
    )
except Exception as e:
    st.warning(f"Could not display file table: {e}")

# ---------------------------------------------------------
# Sidebar - select a file
# ---------------------------------------------------------
file_map = {f"{f['filename']} ({f['id']})": f["id"] for f in files}
selected_file_label = st.sidebar.selectbox("Choose a file to explore", list(file_map.keys()))
file_id = file_map[selected_file_label]

# ---------------------------------------------------------
# Delete option
# ---------------------------------------------------------
st.sidebar.markdown("---")
if st.sidebar.button("🗑 Delete This File"):
    try:
        delete_resp = requests.delete(f"{API_BASE}/v1/files/{file_id}")
        if delete_resp.status_code == 200 and delete_resp.json().get("success"):
            st.sidebar.success("File deleted successfully!")
            st.rerun()
        else:
            st.sidebar.error("Failed to delete file.")
    except Exception as e:
        st.sidebar.error(f"Error deleting file: {e}")

# ---------------------------------------------------------
# Load rows from selected file
# ---------------------------------------------------------
st.subheader(f"📚 Records for: {selected_file_label}")

try:
    rows_resp = requests.get(f"{API_BASE}/v1/files/{file_id}/rows")
    rows = rows_resp.json().get("data", [])
except Exception as e:
    st.error(f"❌ Unable to fetch rows: {e}")
    st.stop()

if not rows:
    st.warning("This file does not contain any row data.")
    st.stop()

df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True)

# ---------------------------------------------------------
# Summary Stats
# ---------------------------------------------------------
st.header("📈 Summary Statistics")

try:
    summary = requests.get(f"{API_BASE}/v1/analysis/summary", params={"file_id": file_id}).json()
    st.json(summary.get("data", {}))
except:
    st.warning("Could not load summary statistics.")

# ---------------------------------------------------------
# Column Filters
# ---------------------------------------------------------
st.header("🎛 Filter Data")

numeric_cols = df.select_dtypes(include="number").columns.tolist()
text_cols = df.select_dtypes(include="object").columns.tolist()

selected_col = st.selectbox("Filter column", numeric_cols + text_cols)

if selected_col:
    st.write(f"Filtering on: **{selected_col}**")

    if selected_col in numeric_cols:
        min_val, max_val = st.slider(
            "Value range",
            float(df[selected_col].min()),
            float(df[selected_col].max()),
            (float(df[selected_col].min()), float(df[selected_col].max()))
        )
        filtered_df = df[(df[selected_col] >= min_val) & (df[selected_col] <= max_val)]
    else:
        keyword = st.text_input("Keyword filter")
        filtered_df = df[df[selected_col].astype(str).str.contains(keyword, case=False)] if keyword else df

    st.dataframe(filtered_df, use_container_width=True)

    csv = filtered_df.to_csv(index=False).encode()
    st.download_button(
        "⬇ Download Filtered CSV",
        data=csv,
        file_name=f"{selected_col}_filtered.csv",
        mime="text/csv"
    )

# ---------------------------------------------------------
# Visualizations
# ---------------------------------------------------------
st.header("📊 Visualizations")

try:
    plots_resp = requests.get(f"{API_BASE}/v1/analysis/plots", params={"file_id": file_id})
    plots = plots_resp.json().get("data", {})
except:
    plots = {}
    st.warning("No plots available.")

if plots:
    for col, plot_data in plots.items():
        st.subheader(f"Histogram: {col}")
        fig = px.bar(x=plot_data["bins"], y=plot_data["counts"])
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# Ask AI About the Dataset
# ---------------------------------------------------------
st.header("🤖 AI Insights")

question = st.text_input("Ask a question about the data")

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

