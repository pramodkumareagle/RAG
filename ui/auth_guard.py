import streamlit as st

def require_auth():
    if "token" not in st.session_state:
        st.warning("Please login")
        st.page_link("app.py", label="Go to Login")
        st.stop()

def auth_headers():
    return {
        "Authorization": f"Bearer {st.session_state['token']}"
    }

def logout():
    st.session_state.clear()
    st.rerun()