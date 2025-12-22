import streamlit as st
from auth_api import login

st.set_page_config(page_title="RAG Login", page_icon="🔐")

if "token" in st.session_state:
    st.page_link("pages/1_Upload_File.py", label="🚀 Go to App")
    st.stop()

st.title("🔐 Login")

email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Login"):
    try:
        res = login(email, password)
        st.session_state["token"] = res["access_token"]
        st.success("Login successful")
        st.rerun()
    except Exception as e:
        st.error(str(e))

st.divider()
st.page_link("pages/Signup.py", label="Create new account →")
