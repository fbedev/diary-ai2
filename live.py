
"""Streamlit application for the Diary-AI2 experience."""

from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import streamlit as st


API_URL = "http://localhost:8000"


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def ensure_session_state() -> None:
    """Guarantee that frequently used session keys exist."""

    defaults = {
        "token": None,
        "user": None,
        "chat_history": [],
        "latest_summary": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def get_headers() -> Dict[str, str]:
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def api_post(endpoint: str, data: Dict[str, Any]) -> requests.Response:
    return requests.post(f"{API_URL}{endpoint}", json=data, headers=get_headers(), timeout=30)


def api_get(endpoint: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
    return requests.get(f"{API_URL}{endpoint}", params=params, headers=get_headers(), timeout=30)


def display_timeline(entries: List[Dict[str, Any]]) -> None:
    """Render diary entries with a timeline-style layout."""

    if not entries:
        st.info("No diary entries yet. Chat with the assistant to build your timeline!")
        return

    for entry in entries:
        created_at = entry.get("created_at") or entry.get("timestamp")
        mood = entry.get("mood", "–").title()
        tags = entry.get("tags") or entry.get("highlights", [])
        summary = entry.get("summary") or entry.get("content") or ""
        raw = entry.get("raw") or entry.get("messages")

        with st.container():
            st.markdown("---")
            cols = st.columns([0.2, 0.8])
            with cols[0]:
                st.markdown(
                    f"**{mood}**\n\n"
                    f":material/calendar_month: {created_at if created_at else 'Unknown date'}"
                )
                if tags:
                    tag_str = "  ".join(f"`{tag}`" for tag in tags)
                    st.caption(tag_str)
            with cols[1]:
                st.write(summary)
                if raw:
                    with st.expander("View raw conversation"):
                        if isinstance(raw, list):
                            for message in raw:
                                author = message.get("role", "user").title()
                                st.write(f"**{author}:** {message.get('content', '')}")
                        else:
                            st.write(raw)


def parse_entries(entries: List[Dict[str, Any]]) -> pd.DataFrame:
    """Convert diary entries into a dataframe for charts and filters."""

    if not entries:
        return pd.DataFrame()

    normalized = []
    for entry in entries:
        created_at = entry.get("created_at") or entry.get("timestamp") or ""
        mood = entry.get("mood", "Unknown")
        summary = entry.get("summary") or entry.get("content", "")
        normalized.append({
            "created_at": created_at,
            "mood": mood,
            "summary": summary,
        })

    df = pd.DataFrame(normalized)
    if not df.empty:
        try:
            df["created_at"] = pd.to_datetime(df["created_at"])
        except (ValueError, TypeError):
            pass
    return df


def require_login() -> bool:
    if st.session_state.get("token"):
        return True
    st.warning("Please login first to access this section.")
    return False


def show_login_signup() -> None:
    st.title("Diary-AI2 ✨")
    st.caption("Your conversational diary that crafts summaries and mood timelines automatically.")

    tab_login, tab_signup = st.tabs([":material/login: Login", ":material/person_add: Sign up"])

    with tab_login:
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("Username", placeholder="jane.doe")
            password = st.text_input("Password", type="password")
            remember = st.checkbox("Remember me", value=True)
            submitted = st.form_submit_button("Sign in")

        if submitted:
            if not username or not password:
                st.error("Please provide both username and password.")
            else:
                with st.spinner("Authenticating..."):
                    res = api_post("/auth/login", {"username": username, "password": password})
                if res.status_code == 200:
                    payload = res.json()
                    st.session_state["token"] = payload.get("token")
                    st.session_state["user"] = {
                        "username": username,
                        "remember": remember,
                    }
                    st.success("Welcome back! You are now logged in.")
                    st.toast("Logged in successfully", icon="✅")
                else:
                    st.error(res.json().get("detail", "Login failed. Please try again."))

    with tab_signup:
        with st.form("signup_form", clear_on_submit=True):
            username = st.text_input("Choose a username", key="signup_username")
            password = st.text_input("Create a password", type="password", key="signup_password")
            confirm = st.text_input("Confirm password", type="password", key="signup_confirm")
            submitted = st.form_submit_button("Create account")

        if submitted:
            if not username or not password:
                st.error("Username and password are required.")
            elif password != confirm:
                st.error("Passwords do not match.")
            else:
                with st.spinner("Creating account..."):
                    res = api_post("/auth/signup", {"username": username, "password": password})
                if res.status_code == 200:
                    st.success("Account created! Please head to the login tab.")
                else:
                    st.error(res.json().get("detail", "Signup failed."))


def render_diary_page() -> None:
    if not require_login():
        return

    st.title("Daily Chat & Diary")
    st.caption("Capture conversations, generate AI summaries, and reflect on your day.")

    col_chat, col_summary = st.columns((0.55, 0.45))
    with col_chat:
        st.subheader("Chat with your AI diarist")
        st.write("Use the chat composer below to talk about your day. The assistant will weave it into your diary automatically.")

        prompt = st.chat_input("Share something that happened today...")
        if prompt:
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.spinner("Sending to diary..."):
                res = api_post("/diary/add", {"entry": prompt})
            if res.status_code == 200:
                payload = res.json()
                summary = payload.get("summary") or payload.get("message")
                if summary:
                    st.session_state.latest_summary = summary
                st.toast("Entry saved to your diary", icon="📝")
            else:
                st.error(res.json().get("detail", "Unable to store your note."))

        for message in st.session_state.chat_history[-8:]:
            with st.chat_message(message["role"]):
                st.write(message.get("content", ""))

    with col_summary:
        st.subheader("Latest AI summary")
        if st.session_state.latest_summary:
            st.success(st.session_state.latest_summary)
        else:
            st.info("Your summaries will appear here after you chat about your day.")

        st.divider()
        st.subheader("Mood snapshot")
        timeline_res = api_get("/diary/list")
        entries = timeline_res.json().get("entries", []) if timeline_res.status_code == 200 else []
        df = parse_entries(entries)
        if not df.empty and "created_at" in df:
            grouped = df.groupby("mood").size().reset_index(name="count")
            st.dataframe(grouped, use_container_width=True)
        else:
            st.caption("Mood analytics will populate after a few diary entries.")

    st.divider()
    st.subheader("Timeline")
    col_filters = st.columns(3)
    selected_mood = col_filters[0].selectbox(
        "Filter by mood", ["All"] + sorted({e.get("mood", "Unknown") for e in entries})
    )
    start_date = col_filters[1].date_input("From", value=dt.date.today() - dt.timedelta(days=7))
    end_date = col_filters[2].date_input("To", value=dt.date.today())

    filtered_entries: List[Dict[str, Any]] = []
    for entry in entries:
        created_at = entry.get("created_at") or entry.get("timestamp")
        if created_at:
            try:
                created_dt = pd.to_datetime(created_at).date()
            except (ValueError, TypeError):
                created_dt = None
        else:
            created_dt = None

        within_range = True
        if created_dt is not None:
            within_range = start_date <= created_dt <= end_date

        mood_matches = selected_mood == "All" or entry.get("mood", "Unknown") == selected_mood

        if within_range and mood_matches:
            filtered_entries.append(entry)

    display_timeline(filtered_entries)


def render_search_page() -> None:
    if not require_login():
        return

    st.title("Search & Rediscover")
    st.caption("Look up past moments by keyword, mood, or date range.")

    with st.form("search_form"):
        query = st.text_input("Keyword or phrase", placeholder="coffee with Alex")
        mood = st.text_input("Mood filter", placeholder="joyful")
        start = st.date_input("Start date", value=dt.date.today() - dt.timedelta(days=30))
        end = st.date_input("End date", value=dt.date.today())
        submitted = st.form_submit_button("Search diary")

    if submitted:
        payload = {"query": query}
        if mood:
            payload["mood"] = mood
        payload["start_date"] = start.isoformat()
        payload["end_date"] = end.isoformat()

        with st.spinner("Searching your memories..."):
            res = api_post("/search", payload)

        if res.status_code == 200:
            results = res.json().get("results", [])
            if not results:
                st.info("No entries found. Try adjusting your filters.")
            else:
                for item in results:
                    with st.expander(item.get("title") or item.get("summary", "Entry")):
                        st.write(item.get("summary", ""))
                        st.caption(item.get("created_at", ""))
        else:
            st.error(res.json().get("detail", "Search failed."))


def render_admin_page() -> None:
    if not require_login():
        return

    st.title("Admin dashboard")
    st.caption("Monitor user activity and session health.")

    cols = st.columns(3)
    users_res = api_get("/admin/users")
    sessions_res = api_get("/admin/sessions")

    if users_res.status_code == 200:
        users_data = users_res.json().get("users", users_res.json())
        user_count = len(users_data) if isinstance(users_data, list) else len(users_data.keys())
        cols[0].metric("Total users", user_count)
        with st.expander("User list"):
            st.json(users_data)
    else:
        cols[0].error("Unable to load users")

    if sessions_res.status_code == 200:
        sessions_data = sessions_res.json().get("sessions", sessions_res.json())
        session_count = len(sessions_data) if isinstance(sessions_data, list) else len(sessions_data.keys())
        cols[1].metric("Active sessions", session_count)
        with st.expander("Session details"):
            st.json(sessions_data)
    else:
        cols[1].error("Unable to load sessions")

    audit_res = api_get("/diary/list")
    if audit_res.status_code == 200:
        entries = audit_res.json().get("entries", [])
        cols[2].metric("Total diary entries", len(entries))
    else:
        cols[2].error("Unable to load diary stats")


def render_logout() -> None:
    st.session_state.clear()
    st.success("You have been logged out. See you soon!")


def main() -> None:
    st.set_page_config(
        page_title="Diary-AI2",
        page_icon="📓",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    ensure_session_state()

    st.sidebar.image(
        "https://avatars.githubusercontent.com/u/131082196?s=200&v=4",
        width=64,
        caption="Diary-AI2",
    )
    st.sidebar.title("Navigation")

    is_authenticated = st.session_state.get("token") is not None
    options = ["Diary", "Search", "Admin", "Logout"] if is_authenticated else ["Login"]
    page = st.sidebar.radio("", options, index=0)

    if is_authenticated:
        user = st.session_state.get("user", {})
        st.sidebar.success(f"Signed in as {user.get('username', 'user')}")
        st.sidebar.caption("Tip: New chats instantly appear in your timeline.")
        st.sidebar.divider()
        st.sidebar.markdown("**Quick links**")
        st.sidebar.button("Refresh timeline", on_click=lambda: None)
    else:
        st.sidebar.info("Login to unlock diary, search, and admin views.")

    if page == "Login":
        show_login_signup()
    elif page == "Diary":
        render_diary_page()
    elif page == "Search":
        render_search_page()
    elif page == "Admin":
        render_admin_page()
    elif page == "Logout":
        render_logout()


if __name__ == "__main__":
    main()
