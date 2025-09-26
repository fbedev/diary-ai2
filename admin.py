import streamlit as st
import sqlite3

def admin_dashboard():
    st.header("Admin Portal")
    conn = sqlite3.connect("data/users.db")
    cur = conn.cursor()
    cur.execute("SELECT id, username, role FROM users")
    users = cur.fetchall()
    conn.close()

    st.write("### Registered Users")
    for u in users:
        st.write(f"ID: {u[0]} | Username: {u[1]} | Role: {u[2]}")