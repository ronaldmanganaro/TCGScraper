import streamlit as st

# Hardcoded credentials (replace with env vars or secure storage in real apps)
USER_CREDENTIALS = {
    "admin": "password123",
    "ronald": "securepass"
}

def login():
    st.title("🔐 Login")

    # Show login form if not logged in
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Welcome, {username}!")
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")
        return False
    return True

# Main app logic
if login():
    st.title("📊 TCG Tools Dashboard")
    st.write("You're now logged in.")
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
