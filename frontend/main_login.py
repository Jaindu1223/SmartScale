import streamlit as st

# Set page config once at the very beginning
st.set_page_config(page_title="SmartScale Login", layout="centered")

# --- 1. SESSION STATE SETUP ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- 2. LOGIN SCREEN ---
def login_page():
    st.title("🔐 Welcome to SmartScale")
    st.markdown("Please log in to access your MLOps Dashboard.")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            # Hardcoded for your University Demo (You can add a database later)
            if username == "admin" and password == "smartscale2026":
                st.session_state['logged_in'] = True
                st.success("Login successful!")
                st.rerun()  # Instantly reloads the page to show the dashboard
            else:
                st.error("❌ Incorrect username or password.")

# --- 3. MAIN ROUTER ---
if not st.session_state['logged_in']:
    # Show the login screen if they aren't authenticated
    login_page()
else:
    # If they are logged in, hide the login screen and load the real dashboard!
    
    # Add a logout button to the sidebar
    if st.sidebar.button("🚪 Logout"):
        st.session_state['logged_in'] = False
        st.rerun()
        
    # Import and run your actual dashboard code
    import dashboard_core