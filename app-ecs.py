import streamlit as st
import json
import boto3
from utils.auth import Auth
from utils.llm import Llm
from config_file import Config

from dotenv import load_dotenv
import logging
import logging.config
import re
from services import bedrock_agent_runtime
import uuid
import yaml
import os

from datetime import datetime
from streamlit_cognito_auth import CognitoAuthenticator

ui_title = os.getenv('BEDROCK_AGENT_TEST_UI_TITLE', 'Welcome to CenITex Modern Cloud Cost Calculator Powered by AI')
ui_icon = os.getenv('BEDROCK_AGENT_TEST_UI_ICON', '🤖')
agent_id = Config.BEDROCK_AGENT_ID
agent_alias_id = Config.BEDROCK_AGENT_ALIAS_ID

# ID of Secrets Manager containing cognito parameters
SECRETS_MANAGER_ID = Config.SECRETS_MANAGER_ID

# ID of the AWS region in which Secrets Manager is deployed
AWS_REGION = Config.DEPLOYMENT_REGION

class Auth:
    @staticmethod
    def get_authenticator(secret_id, region):
        """Get Cognito parameters from Secrets Manager and return CognitoAuthenticator"""
        try:
            secretsmanager_client = boto3.client("secretsmanager", region_name=region)
            response = secretsmanager_client.get_secret_value(SecretId=secret_id)
            secret_string = json.loads(response['SecretString'])
            
            pool_id = secret_string['pool_id']
            app_client_id = secret_string['app_client_id']
            app_client_secret = secret_string['app_client_secret']
            
            authenticator = CognitoAuthenticator(
                pool_id=pool_id,
                app_client_id=app_client_id,
                app_client_secret=app_client_secret,
            )
            
            return authenticator
        except Exception as e:
            st.error(f"Failed to initialize authenticator: {str(e)}")
            return None

def load_css():
    st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background: linear-gradient(135deg, #e8e3f0 0%, #d4c5e8 100%);
    }
    
    .main-header {
        background: #452c63;
        padding: 0.8rem 1.2rem;
        border-radius: 10px;
        margin: 0 0 0.5rem 0;
        text-align: left;
        color: white;
        max-width: 600px;
        box-shadow: 0 4px 15px rgba(69, 44, 99, 0.3);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 1.4rem;
        font-weight: 600;
    }
    
    .main-header p {
        margin: 0.3rem 0 0 0;
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.8rem;
        border-radius: 10px;
        margin: 0.2rem 0;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        max-width: 80%;
    }
    
    .assistant-message {
        background: white;
        color: #2c3e50;
        padding: 0.8rem;
        border-radius: 10px;
        margin: 0.2rem 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        max-width: 80%;
    }
    
    /* Main chat input - keep bold black styling */
    .stTextInput > div > div > input {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%) !important;
        color: #FFFFFF !important;
        border: 10px solid #000000 !important;
        border-radius: 35px !important;
        padding: 30px 50px !important;
        font-size: 24px !important;
        font-weight: 900 !important;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.7) !important;
        transition: all 0.3s ease !important;
        min-height: 90px !important;
    }
    
    .main .block-container {
        padding-left: 1rem !important;
        margin-left: 0 !important;
        padding-bottom: 150px !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #000000 !important;
        box-shadow: 0 0 40px rgba(0, 0, 0, 0.7) !important;
        transform: translateY(-4px) !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #ffffff !important;
        font-weight: 800 !important;
    }
    
    /* Login form styling - lighter colors */
    .stForm .stTextInput > div > div > input {
        background: #f8f9fa !important;
        color: #2c3e50 !important;
        border: 2px solid #dee2e6 !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        font-size: 16px !important;
        font-weight: 400 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
        min-height: auto !important;
        transform: none !important;
    }
    
    .stForm .stTextInput > div > div > input:focus {
        border-color: #452c63 !important;
        box-shadow: 0 0 0 3px rgba(69, 44, 99, 0.1) !important;
        transform: none !important;
    }
    
    .stForm .stTextInput > div > div > input::placeholder {
        color: #6c757d !important;
        font-weight: 400 !important;
    }
    
    /* Cognito login form specific styling */
    div[data-testid="stForm"] .stTextInput > div > div > input {
        background: #f8f9fa !important;
        color: #2c3e50 !important;
        border: 2px solid #dee2e6 !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        font-size: 16px !important;
        font-weight: 400 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
        min-height: auto !important;
        transform: none !important;
    }
    
    div[data-testid="stForm"] .stTextInput > div > div > input:focus {
        border-color: #452c63 !important;
        box-shadow: 0 0 0 3px rgba(69, 44, 99, 0.1) !important;
        transform: none !important;
    }
    
    div[data-testid="stForm"] .stTextInput > div > div > input::placeholder {
        color: #6c757d !important;
        font-weight: 400 !important;
    }
    </style>
    """, unsafe_allow_html=True)

def init_session_state():
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'citations' not in st.session_state:
        st.session_state.citations = []
    if 'trace' not in st.session_state:
        st.session_state.trace = {}
    if 'message_count' not in st.session_state:
        st.session_state.message_count = 0
    if 'session_start_time' not in st.session_state:
        st.session_state.session_start_time = datetime.now()
    if 'auth_status' not in st.session_state:
        st.session_state.auth_status = None
    if 'logout_clicked' not in st.session_state:
        st.session_state.logout_clicked = False

def display_chat_message(message, is_user=False):
    message_class = "user-message" if is_user else "assistant-message"
    icon = "👤" if is_user else "🤖"
    
    st.markdown(f"""
    <div class="{message_class}">
        <strong>{icon} {'You' if is_user else 'AI Cost Calculator'}</strong>
        <div style="margin-top: 0.5rem;">
            {message}
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_authenticated_app(authenticator):
    """Display the main app for authenticated users"""
    
    def logout():
        st.session_state.logout_clicked = True
        st.session_state.auth_status = None
        authenticator.logout()
        st.rerun()
    
    with st.sidebar:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=200)
            st.divider()
        
        st.title("🎛️ Control Panel")
        
        st.subheader(f"👤 Welcome, {authenticator.get_username()}")
        st.button("🚪 Logout", key="logout_btn", on_click=logout, use_container_width=True)
        
        st.divider()
        
        st.subheader("🤖 Agent Status")
        status = "🟢 Online" if agent_id else "🔴 Offline"
        st.success(f"Status: {status}")
        st.info(f"Messages: {st.session_state.message_count}")
        
        st.divider()
        
        st.subheader("📱 Session Controls")
        if st.button("🔄 New Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.message_count = 0
            st.session_state.citations = []
            st.session_state.trace = {}
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.session_start_time = datetime.now()
            st.rerun()
        
        st.divider()
        
        st.subheader("Save chat history?")
        if st.session_state.messages:
            chat_data = {
                "session_id": st.session_state.session_id,
                "timestamp": datetime.now().isoformat(),
                "messages": st.session_state.messages,
                "message_count": st.session_state.message_count,
                "user": authenticator.get_username()
            }
            
            st.download_button(
                label="📄 Download Chat History",
                data=json.dumps(chat_data, indent=2),
                file_name=f"chat_history_{authenticator.get_username()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        else:
            st.info("No chat history available")
    
    # MAIN CONTENT
    st.markdown(f"""
    <div class="main-header">
        <h1>{ui_icon} {ui_title}</h1>
        <p>Calculate Hosting costs based on Support Type and Cloud Consumption</p>
    </div>
    """, unsafe_allow_html=True)
    
    for message in st.session_state.messages:
        if message["role"] == "user":
            display_chat_message(message["content"], is_user=True)
        else:
            display_chat_message(message["content"], is_user=False)
    
    st.markdown("<div style='height: 300px;'></div>", unsafe_allow_html=True)
    
    if prompt := st.chat_input("Please start by typing preferred cloud platform, support type and estimated consumption costs"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.message_count += 1
        
        display_chat_message(prompt, is_user=True)
        
        # Check if agent configuration is available
        if not agent_id or not agent_alias_id:
            st.error("❌ Bedrock Agent not configured. Please set BEDROCK_AGENT_ID and BEDROCK_AGENT_ALIAS_ID environment variables.")
            return
        
        try:
            with st.spinner("🤔 Processing your request..."):
                response = bedrock_agent_runtime.invoke_agent(
                    agent_id,
                    agent_alias_id,
                    st.session_state.session_id,
                    prompt
                )
            
            output_text = response["output_text"]
            
            if not output_text or output_text.strip() == "":
                output_text = "I apologize, but I couldn't generate a response. Please try rephrasing your question."
            
            try:
                output_json = json.loads(output_text, strict=False)
                if "instruction" in output_json and "result" in output_json:
                    output_text = output_json["result"]
            except json.JSONDecodeError:
                pass
            
            st.session_state.messages.append({"role": "assistant", "content": output_text})
            st.session_state.citations = response["citations"]
            st.session_state.trace = response["trace"]
            
            display_chat_message(output_text, is_user=False)
            
        except Exception as e:
            error_msg = str(e)
            st.error(f"❌ Error invoking Bedrock Agent: {error_msg}")
            
            if "AccessDenied" in error_msg:
                st.info("📝 Check your AWS credentials and IAM permissions for Bedrock Agent access.")
            elif "ResourceNotFound" in error_msg:
                st.info("📝 Verify your BEDROCK_AGENT_ID and BEDROCK_AGENT_ALIAS_ID are correct.")
            elif "ValidationException" in error_msg:
                st.info("📝 Check that your agent is deployed and the alias exists.")
            else:
                st.info("📝 Please check your AWS configuration and network connection.")
            
            fallback_response = "I'm currently unable to process your request due to a technical issue. Please try again later or contact support."
            st.session_state.messages.append({"role": "assistant", "content": fallback_response})
            display_chat_message(fallback_response, is_user=False)

def main():
    st.set_page_config(
        page_title=ui_title,
        page_icon=ui_icon,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    init_session_state()
    load_css()
    
    # Initialize authenticator
    authenticator = Auth.get_authenticator(SECRETS_MANAGER_ID, AWS_REGION)

    if authenticator is None:
        st.error("❌ Failed to initialize authentication. Please check your AWS Secrets Manager configuration.")
        st.info("📝 Ensure SECRETS_MANAGER_ID environment variable is set and the secret exists in AWS Secrets Manager.")
        st.stop()
    
    # Handle logout
    if st.session_state.logout_clicked:
        st.session_state.logout_clicked = False
        st.rerun()
    
    # Authenticate user
    is_logged_in = authenticator.login()
    
    # Handle login state changes
    if is_logged_in != st.session_state.auth_status:
        st.session_state.auth_status = is_logged_in
        if is_logged_in:
            st.rerun()
    
    if not is_logged_in:
        st.markdown("""
        <div class="main-header" style="max-width: 500px; margin: 2rem auto; text-align: center;">
            <h1>🔐 CenITex AI Cost Calculator</h1>
            <p>Please login to access the AI-powered cloud cost calculator</p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()
    
    # Display main app for authenticated users
    display_authenticated_app(authenticator)

if __name__ == "__main__":
    main()