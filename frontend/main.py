import streamlit as st

# Setup the page (MUST be the first Streamlit command)
st.set_page_config(page_title="SmartScale Platform", layout="wide")

# Session State Initialization
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# Create the Login Function
def login_screen():
    st.markdown("<h1 style='text-align: center;'>🔐 Welcome to SmartScale</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Please log in to access the Autonomic Cloud Manager.</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Placing the form inside columns to keep it narrow and centered on the screen
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                if username == "admin" and password == "admin":
                    st.session_state['logged_in'] = True
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")

# page difinitations
# pass the login_screen as a function, and the others as file paths!
login_page = st.Page(login_screen, title="Login", icon="🔐")
home_page = st.Page("views/1_home.py", title="Live Dashboard", icon="📊")
deploy_page = st.Page("views/2_deploy.py", title="Deploy Model", icon="🚀")
settings_page = st.Page("views/3_settings.py", title="Cloud Settings", icon="⚙️")

# Dynamic Navigation Routing
if not st.session_state['logged_in']:
    # SECURITY LOCK: If logged out, only the login page exists in the system.
    # Streamlit automatically hides the sidebar completely when there is only 1 page!
    pg = st.navigation([login_page])
else:
    # IF LOGGED IN: Unlock the full application and group the menus nicely!
    pg = st.navigation({
        "Autonomic Manager": [home_page, deploy_page],
        "System Configuration": [settings_page]
    })
    
    # Add a custom logout button to the bottom of the sidebar
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state['logged_in'] = False
        st.rerun()

# 6. Execute the router
pg.run()