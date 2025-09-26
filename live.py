
import streamlit as st
import requests

API_URL = "http://localhost:8000"

# --- Helpers ---
def get_headers():
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def api_post(endpoint, data):
    return requests.post(f"{API_URL}{endpoint}", json=data, headers=get_headers())

def api_get(endpoint):
    return requests.get(f"{API_URL}{endpoint}", headers=get_headers())

# --- Sidebar Navigation ---
st.sidebar.title("ChatDiary Pro")
page = st.sidebar.radio("Navigate", ["Login", "Signup", "Diary", "Search", "Admin", "Logout"])

# --- Login ---
if page == "Login":
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        res = api_post("/auth/login", {"username": username, "password": password})
        if res.status_code == 200:
            st.session_state["token"] = res.json()["token"]
            st.session_state["user"] = username
            st.success("Logged in successfully!")
        else:
            st.error(res.json().get("detail", "Login failed"))

# --- Signup ---
elif page == "Signup":
    st.title("Signup")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Signup"):
        res = api_post("/auth/signup", {"username": username, "password": password})
        if res.status_code == 200:
            st.success("User created successfully, please login.")
        else:
            st.error(res.json().get("detail", "Signup failed"))

# --- Diary ---
elif page == "Diary":
    st.title("Diary")
    if "token" not in st.session_state:
        st.warning("Please login first.")
    else:
        entry = st.text_area("Write your diary entry")
        if st.button("Save Entry"):
            res = api_post("/diary/add", {"entry": entry})
            if res.status_code == 200:
                st.success("Entry saved!")
            else:
                st.error("Failed to save entry")
        st.subheader("Your Entries")
        res = api_get("/diary/list")
        if res.status_code == 200:
            for e in res.json().get("entries", []):
                st.write(f"- {e}")

# --- Search ---
elif page == "Search":
    st.title("Search Diary")
    if "token" not in st.session_state:
        st.warning("Please login first.")
    else:
        query = st.text_input("Search query")
        if st.button("Search"):
            res = api_post("/search", {"query": query})
            if res.status_code == 200:
                results = res.json().get("results", [])
                for r in results:
                    st.write(r)
            else:
                st.error("Search failed")

# --- Admin ---
elif page == "Admin":
    st.title("Admin Dashboard")
    if "token" not in st.session_state:
        st.warning("Please login first.")
    else:
        st.subheader("Users")
        res = api_get("/admin/users")
        if res.status_code == 200:
            st.json(res.json())

        st.subheader("Sessions")
        res = api_get("/admin/sessions")
        if res.status_code == 200:
            st.json(res.json())

# --- Logout ---
elif page == "Logout":
    st.session_state.clear()
    st.success("Logged out successfully.")
