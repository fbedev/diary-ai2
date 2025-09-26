import streamlit as st
from app.admin import admin_dashboard
import os, redis

def run_streamlit():
    st.set_page_config(page_title="ChatDiary Pro", layout="centered")
    if "user" not in st.session_state:
        st.session_state.user = None

    user_dict = {"username": "ethan", "role": "admin"}

    if st.session_state.user is None:
        st.title("ChatDiary Pro")
        tab1, tab2 = st.tabs(["Sign Up", "Login"])

        with tab1:
            with st.form("signup_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign Up")
                if submitted:
                    st.success("Account created (demo)")

        with tab2:
            with st.form("login_form"):
                username = st.text_input("Username", key="login_user")
                password = st.text_input("Password", type="password", key="login_pass")
                submitted = st.form_submit_button("Login")
                if submitted:
                    if username == "ethan" and password == "password":
                        st.session_state.user = user_dict
                        st.experimental_rerun()
                    else:
                        st.error("Invalid credentials")
    else:
        user = st.session_state.user
        st.sidebar.write(f"Welcome, {user['username']} ({user['role']})")
        if st.sidebar.button("Logout"):
            st.session_state.user = None
            st.experimental_rerun()

        if user["role"] == "admin":
            admin_dashboard()
        else:
            st.write("📖 Your Diary (user portal here)")

if __name__ == "__main__":
    run_streamlit()