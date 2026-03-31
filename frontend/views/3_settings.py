import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

st.title("Cloud Environment Settings")
st.markdown("Configure your AWS credentials to allow SmartScale to manage your infrastructure.")

with st.container(border=True):
    aws_access = st.text_input("AWS Access Key", value=st.session_state.get('aws_access', os.getenv("AWS_ACCESS_KEY_ID", "")), type="password")
    aws_secret = st.text_input("AWS Secret Key", value=st.session_state.get('aws_secret', os.getenv("AWS_SECRET_ACCESS_KEY", "")), type="password")
    aws_region = st.text_input("AWS Region", value=st.session_state.get('aws_region', "us-east-1"))
    aws_func = st.text_input("Lambda Function Name", value=st.session_state.get('aws_func', "InferenceFunction"))

    if st.button("💾 Save Settings"):
        st.session_state['aws_access'] = aws_access
        st.session_state['aws_secret'] = aws_secret
        st.session_state['aws_region'] = aws_region
        st.session_state['aws_func'] = aws_func
        st.success("✅ AWS Settings saved securely to your session!")