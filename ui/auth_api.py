import requests
import os
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://localhost:8000")


def login(email: str, password: str):
    r = requests.post(
        f"{API_BASE}/auth/login",
        json={"email": email, "password": password},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def signup(email: str, password: str, full_name: str | None = None):
    r = requests.post(
        f"{API_BASE}/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
        },
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def auth_headers():
    return {
        "Authorization": f"Bearer {st.session_state['token']}"
    }
