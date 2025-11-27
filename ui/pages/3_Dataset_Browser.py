import os
import streamlit as st
import requests
import pandas as pd
import numpy as np
import altair as alt

API_BASE = st.secrets.get("API_BASE", os.getenv("API_BASE", "http://api:8000"))

st.set_page_config(page_title="Advanced Dataset Browser", layout="wide")

st.title("📊 Advanced Dataset Browser")
st.markdown("Explore your uploaded datasets with filtering, analysis, charts, and AI insights.")

# ---------------------------------------------------------
# Load uploaded files
# ---------------------------------------------------------
st.sidebar.header("📁 Files")

try:
    resp = requests.get(f"{API_BASE}/v1/files")
    files = resp.json().get("data", [])
except:
    st.error("❌ Unable to load file list.")
    st.stop()

if not files:
    st.info("No files uploaded yet.")
    st.stop()

file_map = {f"{f['filename']} ({f['id']})": f["id"] for f in files}
selected_file = st.sidebar.selectbox("Choose a file", file_map.keys())
file_id = file_map[selected_file]

# ---------------------------------------------------------
# Load rows for selected file
# ---------------------------------------------------------
try:
    resp = requests.get(f"{API_BASE}/v1/files/{file_id}/rows")
    rows = resp.json().get("data", [])
except Exception as e:
    st.error(f"❌ Failed to load rows: {e}")
    st.stop()

if not rows:
    st.warning("No extracted rows for this file.")
    st.stop()

# Group by table/sheet
tables = {}
for row in rows:
    tables.setdefault(row["table_name"], []).append(row)

table_name = st.sidebar.selectbox("Select Table / Sheet", list(tables.keys()))

# ---------------------------------------------------------
# Convert JSON row_data → DataFrame
# ---------------------------------------------------------
df = pd.DataFrame([row["row_data"] for row in tables[table_name]])

st.header(f"📄 Preview: {table_name}")
st.dataframe(df, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------
# 🔍 Search Bar
# ---------------------------------------------------------
st.subheader("🔍 Search in table")

search_term = st.text_input("Search for text in any column")

if search_term:
    df = df[df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]

# ---------------------------------------------------------
# 🎯 Filters by column
# ---------------------------------------------------------
st.subheader("🎛 Column Filters")

with st.expander("Show Filters"):

    for col in df.columns:
        col_data = df[col]

        # -------------------------------------------------
        # Numeric Filter (SAFE)
        # -------------------------------------------------
        if pd.api.types.is_numeric_dtype(col_data):
            if col_data.dropna().empty:
                st.info(f"Column '{col}' has no numeric values.")
                continue

            min_val, max_val = col_data.min(), col_data.max()

            if float(min_val) == float(max_val):
                st.info(f"Column '{col}' has a single value: {min_val}")
            else:
                selected_range = st.slider(
                    f"{col} range",
                    min_value=float(min_val),
                    max_value=float(max_val),
                    value=(float(min_val), float(max_val)),
                )
                df = df[(df[col] >= selected_range[0]) & (df[col] <= selected_range[1])]

        # -------------------------------------------------
        # Date Filter (SAFE)
        # -------------------------------------------------
        elif pd.api.types.is_datetime64_any_dtype(col_data):
            if col_data.dropna().nunique() <= 1:
                st.info(f"Column '{col}' has a single date.")
                continue

            date_min, date_max = col_data.min(), col_data.max()

            date_range = st.date_input(
                f"{col} date range",
                value=[date_min.date(), date_max.date()],
            )

            if len(date_range) == 2:
                start, end = date_range
                df = df[
                    (df[col] >= pd.to_datetime(start)) &
                    (df[col] <= pd.to_datetime(end))
                ]

        # -------------------------------------------------
        # Text filter
        # -------------------------------------------------
        else:
            text_filter = st.text_input(f"Filter {col} contains", key=f"textfilter_{col}")
            if text_filter:
                df = df[df[col].astype(str).str.contains(text_filter, case=False)]

# ---------------------------------------------------------
# 📈 Summary Statistics
# ---------------------------------------------------------
st.subheader("📈 Summary Statistics")

numeric_df = df.select_dtypes(include=[np.number])

if numeric_df.shape[1] > 0:
    st.write(numeric_df.describe())
else:
    st.info("No numeric columns available.")

# ---------------------------------------------------------
# 📊 Auto-generated charts
# ---------------------------------------------------------
st.subheader("📊 Charts")

if df.shape[1] > 1:
    chart_type = st.radio(
        "Choose chart type",
        ["Bar", "Line", "Pie", "Histogram"],
        horizontal=True,
    )

    x_col = st.selectbox("X-axis", df.columns, key="chart_x")
    y_col = st.selectbox("Y-axis", df.columns, key="chart_y")

    if not df.empty:
        try:
            if chart_type == "Bar":
                chart = alt.Chart(df).mark_bar().encode(x=x_col, y=y_col)
                st.altair_chart(chart, use_container_width=True)

            elif chart_type == "Line":
                chart = alt.Chart(df).mark_line().encode(x=x_col, y=y_col)
                st.altair_chart(chart, use_container_width=True)

            elif chart_type == "Pie":
                chart = alt.Chart(df).mark_arc().encode(theta=y_col, color=x_col)
                st.altair_chart(chart, use_container_width=True)

            elif chart_type == "Histogram":
                chart = alt.Chart(df).mark_bar().encode(
                    alt.X(x_col, bin=True),
                    y="count()"
                )
                st.altair_chart(chart, use_container_width=True)

        except Exception as e:
            st.warning(f"Chart rendering failed: {e}")

else:
    st.info("Not enough columns for charts.")

# ---------------------------------------------------------
# 🤖 AI Insights (using your existing Ask API)
# ---------------------------------------------------------
st.markdown("---")
st.subheader("🤖 AI Insights")

prompt = st.text_area("Ask a question about this table:")

if st.button("Ask AI"):
    try:
        payload = {"query": prompt, "top_k": 5}
        resp = requests.post(f"{API_BASE}/v1/ask", json=payload)
        answer = resp.json().get("data", {}).get("answer", "No answer.")
        st.success(answer)
    except Exception as e:
        st.error(f"Error from AI: {e}")

# ---------------------------------------------------------
# ⬇️ Download CSV
# ---------------------------------------------------------
st.markdown("---")
csv_bytes = df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Download Filtered CSV",
    data=csv_bytes,
    file_name=f"{table_name}_filtered.csv",
    mime="text/csv"
)
