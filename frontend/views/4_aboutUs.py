import streamlit as st
import os

# ui setup
st.markdown("<h1 style='text-align: left;margin-bottom: -15px; font-weight: 800; letter-spacing: -0.5px;'>About SmartScale</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: left; color: #b3e5fc; margin-bottom: 35px; font-size: 1.1em;'>The Autonomic Cloud Manager for Next-Gen MLOps.</p>", unsafe_allow_html=True)

# Section 1
st.markdown("### 🌐 What is SmartScale?")
with st.container(border=True):
    st.markdown("""
    SmartScale is an intelligent, serverless MLOps platform built to automate the heavy lifting of deploying and scaling artificial intelligence. 
    Instead of manually guessing how much hardware a machine learning model needs, or reacting too late to traffic spikes, SmartScale handles it autonomously.
    
    It analyzes the deep learning architecture of your PyTorch models, automatically sizes the AWS Lambda infrastructure, and uses a **Proactive LSTM neural network** to predict web traffic and scale resources *before* your users experience latency.
    """)

st.markdown("<br>", unsafe_allow_html=True)

# section 2
st.markdown("### Quick Start Guide")
with st.container(border=True):
    st.markdown("""
    **1. Configure Cloud Credentials**
    Navigate to the **Settings** page. Enter your secure AWS IAM Access Keys and specify your target region and Lambda function.
    
    **2. Deploy your Workload**
    Head over to the **Deploy** page and upload your PyTorch (`.pth`) model. The internal AI will extract the layers, calculate the exact RAM needed, and securely push the artifact to your AWS S3 bucket.
    
    **3. Engage the Autonomic Scaler**
    Once deployed, toggle the **Enable AI** switch in your MLOps Control Plane. This activates the ProactiveLSTM engine to take over infrastructure management.
    
    **4. Monitor Live Telemetry**
    Open the **Dashboard** to watch the AI in action. You will see real-time AWS CloudWatch invocations, predictive traffic mapping, and the live scaling decisions executed on your cloud environment.
    """)

st.markdown("<br>", unsafe_allow_html=True)

# Section 3
st.markdown("### About the Developer")
with st.container(border=True):
    # Using a 1:3 ratio so your image takes up a nice column on the left
    c1, c2 = st.columns([1, 3], gap="large")
    
    with c1:
        dev_image_path = "helper/jaindu.png" 
        
        if os.path.exists(dev_image_path):
            # Using use_container_width makes it perfectly fit the column
            st.image(dev_image_path, use_container_width=True)
        else:
            # A sleek fallback placeholder just in case the image path is wrong
            st.markdown("""
            <div style='background: rgba(0, 212, 255, 0.1); border: 1px solid #00d4ff; border-radius: 10px; height: 180px; display: flex; align-items: center; justify-content: center;'>
                <span style='font-size: 50px;'>👤</span>
            </div>
            """, unsafe_allow_html=True)
            
    with c2:
        st.markdown("<h3 style='margin-top: 35px; margin-bottom: -18px; color: #ffffff;'>Jaindu Gajanayake</h3>", unsafe_allow_html=True)
        st.markdown("<h5 style='color: #00d4ff; margin-top: 0px; margin-bottom: 5px;'>Undergraduate Software Engineer & Cloud Architect</h5>", unsafe_allow_html=True)
        st.markdown("""
        I am a final-year Software Engineering undergraduate student at the University of Westminster, passionate about bridging the gap between intelligent software and robust cloud infrastructure. 
        
        Prior to engineering SmartScale as my final year project, I worked as a Software Engineer at Applova.io, where I gained hands-on experience building scalable, production-grade architectures. My technical focus lies in mobile development, backend microservices, and autonomic computing systems.
        """)