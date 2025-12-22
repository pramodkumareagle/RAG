import streamlit as st
from auth_api import signup

st.set_page_config(page_title="Signup", page_icon="📝")

st.title("📝 Create Account")

email = st.text_input("Email")
full_name = st.text_input("Full name (optional)")
password = st.text_input("Password", type="password")
confirm = st.text_input("Confirm password", type="password")

if st.button("Sign up"):
    if password != confirm:
        st.error("Passwords do not match")
    elif not email or not password:
        st.error("Email and password required")
    else:
        try:
            res = signup(email, password, full_name)
            st.session_state["token"] = res["access_token"]
            st.success("Account created")
            st.rerun()
        except Exception as e:
            st.error(str(e))

st.divider()
st.page_link("./app.py", label="← Back to Login")
