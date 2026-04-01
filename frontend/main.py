import streamlit as st
import os

# 1. Setup the page (MUST be the first Streamlit command)
st.set_page_config(page_title="SmartScale Platform", page_icon="☁️", layout="wide", initial_sidebar_state="collapsed")

# Custome css injection: Gradient, glassmorphism, animations...etc
custom_css = """
<style>
/* The Professional Dark Blue Gradient Background */
.stApp {
    background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    color: #ffffff;
}

.block-container {
    padding-top: 1.5rem !important; /* Pulls the nav bar right to the top */
    padding-bottom: 1rem !important;
}

/* Hide the default Streamlit top header line and sidebar toggle button */
header {visibility: hidden;}
[data-testid="collapsedControl"] {display: none;}

/* Tighten the horizontal divider line */
hr {
    margin-top: 0.5rem !important;
    margin-bottom: 1rem !important;
}

/*  Glassmorphism effect */
[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    padding: 15px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

/* 4. Glassmorphism Navigation & Global Buttons  */
div.stButton > button {
    background: rgba(255, 255, 255, 0.02); 
    backdrop-filter: blur(10px);           
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.15); 
    color: white;
    border-radius: 20px;
    font-size: 16px !important;            
    font-weight: 600 !important;
    padding: 8px 16px !important;           
    min-height: 42px !important;           
    transition: all 0.3s ease;             
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

/* The Magic Hover Highlight */
div.stButton > button:hover {
    background: rgba(0, 212, 255, 0.15) !important; 
    border: 1px solid #00d4ff !important;
    color: #ffffff !important; 
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 212, 255, 0.4); 
}

/* Primary "Secure Login" Button: GLASS-GLOW UI */
div.stButton > button[kind="primary"] {
    background: rgba(255, 255, 255, 0.01); 
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 2px solid rgba(0, 212, 255, 0.4); 
    border-radius: 12px;
    color: white;
    font-weight: 700 !important;
    box-shadow: 0 4px 15px rgba(0, 212, 255, 0.2);
    transition: all 0.3s ease;
}

div.stButton > button[kind="primary"]:hover {
    background: rgba(255, 255, 255, 0.06); 
    border: 2px solid #00d4ff;             
    color: white;
    transform: translateY(-2px);           
    box-shadow: 0 6px 20px rgba(0, 212, 255, 0.4);
}

div.stButton > button[kind="primary"]:active {
    background: rgba(0, 212, 255, 0.2);
    transform: translateY(1px);
}

/*3D SHINING ANIMATED LOGO TEXT*/
.logo-text {
    font-size: 48px;
    font-weight: 1000;
    margin-top: 10px; /* Perfectly centers vertically with the image */
    margin-left: -20px; 
    letter-spacing: 0.5px;
    
    /* 3D Drop Shadow */
    text-shadow: 2px 4px 8px rgba(0, 0, 0, 0.5);
    
    /* The Shining Gradient Background */
    background: linear-gradient(
        110deg, 
        #ffffff 20%, 
        #b3e5fc 40%, 
        #00d4ff 50%, 
        #b3e5fc 60%, 
        #ffffff 80%
    );
    background-size: 200% auto;
    color: transparent;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    
    /* The Continuous Animation */
    animation: shine 4s linear infinite;
}

/* Animation Keyframes for the sweep effect */
@keyframes shine {
    to {
        background-position: 200% center;
    }
}

img {
    image-rendering: -webkit-optimize-contrast;
    image-rendering: crisp-edges;
    transition: transform 1s ease, filter 0.4s ease;
}

img:hover {
    transform: scale(1.2); 
    filter: drop-shadow(0px 5px 2px rgba(0, 212, 255, 0.6));
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)
# -----------------------------------------------------------

# Session State Initialization
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# Create the Login Function
def login_screen():
    st.markdown("<br>", unsafe_allow_html=True) 
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        img_path = "helper/logo.png"
        if os.path.exists(img_path):
            c1, c2, c3 = st.columns([1, 1, 1])
            with c2: st.image(img_path, use_container_width=True)
            st.markdown("<h1 style='text-align: center; margin-top: -15px;'>SmartScale</h1>", unsafe_allow_html=True)
        else:
            st.markdown("<h1 style='text-align: center; color: #00d4ff;'>SmartScale</h1>", unsafe_allow_html=True)
            
        st.markdown("<p style='text-align: center;'>Autonomic Cloud Manager Login</p>", unsafe_allow_html=True)
        
        with st.container(border=True):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.button("Secure Login", use_container_width=True, type="primary")
            
            if submit:
                if username == "admin" and password == "admin":
                    st.session_state['logged_in'] = True
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")

# Page Definitions
login_page = st.Page(login_screen, title="Login")
home_page = st.Page("views/1_home.py", title="Live Dashboard")
deploy_page = st.Page("views/2_deploy.py", title="Deploy Model")
settings_page = st.Page("views/3_settings.py", title="Cloud Settings")
about_page = st.Page("views/4_aboutUs.py", title="About Us")

# Routing and Navigation logic
if not st.session_state['logged_in']:
    pg = st.navigation([login_page], position="hidden")
else:
    with st.container():
        col_logo, col_home, col_deploy, col_set,col_abtus, col_out = st.columns([4, 1, 1, 1, 1, 1])
        
        with col_logo:
            logo_img_col, logo_txt_col = st.columns([1, 3.7], gap="medium")
            
            with logo_img_col:
                img_path = "helper/Streamlit1.png"
                if os.path.exists(img_path):
                    st.image(img_path) 
            
            with logo_txt_col:
                st.markdown("<div class='logo-text'>SmartScale</div>", unsafe_allow_html=True)
                
        with col_home:
            st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
            if st.button("Dashboard", use_container_width=True): st.switch_page(home_page)
            
        with col_deploy:
            st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
            if st.button("Deploy", use_container_width=True): st.switch_page(deploy_page)
            
        with col_set:
            st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
            if st.button("Settings", use_container_width=True): st.switch_page(settings_page)
        
        with col_abtus:
            st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
            if st.button("About Us", use_container_width=True): st.switch_page(about_page)
        
        with col_out:
            st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
            if st.button("Logout", use_container_width=True):
                st.session_state['logged_in'] = False
                st.rerun()
                
    st.markdown("---") 
    
    pg = st.navigation([home_page, deploy_page, settings_page,about_page], position="hidden")

# Execute the router
pg.run()