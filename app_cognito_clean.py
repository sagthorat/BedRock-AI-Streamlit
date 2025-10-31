from dotenv import load_dotenv
import json
import os
from services import bedrock_agent_runtime
import streamlit as st
import uuid
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

# Cognito configuration
COGNITO_USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
COGNITO_CLIENT_ID = os.getenv('COGNITO_CLIENT_ID')
AWS_REGION = os.getenv('AWS_REGION', 'ap-southeast-2')

# App configuration
agent_id = os.getenv('BEDROCK_AGENT_ID')
agent_alias_id = os.getenv('BEDROCK_AGENT_ALIAS_ID')
ui_title = os.getenv('BEDROCK_AGENT_TEST_UI_TITLE', 'Welcome to CenITex Modern Cloud Cost Calculator Powered by AI')
ui_icon = os.getenv('BEDROCK_AGENT_TEST_UI_ICON', '🤖')

# Initialize Cognito client
cognito_client = boto3.client('cognito-idp', region_name=AWS_REGION)

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
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'access_token' not in st.session_state:
        st.session_state.access_token = ""

def authenticate_user(username, password):
    """Authenticate user with Amazon Cognito"""
    try:
        response = cognito_client.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        if 'AuthenticationResult' in response:
            return True, response['AuthenticationResult']['AccessToken']
        else:
            return False, "Authentication failed"
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NotAuthorizedException':
            return False, "Invalid username or password"
        elif error_code == 'UserNotConfirmedException':
            return False, "User account not confirmed"
        else:
            return False, f"Authentication error: {error_code}"
    except Exception as e:
        return False, f"Connection error: {str(e)}"

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

def cognito_login():
    """Cognito login form"""
    st.markdown("""
    <div class="main-header" style="max-width: 500px; margin: 2rem auto; text-align: center;">
        <h1>🔐 CenITex AI Cost Calculator</h1>
        <p>Please login with your Cognito credentials</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("cognito_login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            col_a, col_b = st.columns(2)
            
            with col_a:
                login_button = st.form_submit_button("Login", use_container_width=True)
            with col_b:
                skip_button = st.form_submit_button("Skip Auth", use_container_width=True)
            
            if login_button and username and password:
                with st.spinner("Authenticating..."):
                    success, result = authenticate_user(username, password)
                    
                if success:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.access_token = result
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error(f"Login failed: {result}")
            elif login_button:
                st.error("Please enter both username and password")
            
            if skip_button:
                st.session_state.authenticated = True
                st.session_state.username = "test_user"
                st.session_state.access_token = "test_token"
                st.rerun()

def display_authenticated_app():
    """Display the main app"""
    
    with st.sidebar:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=200)
            st.divider()
        
        st.title("🎛️ Control Panel")
        
        st.subheader(f"👤 Welcome, {st.session_state.username}")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.session_state.access_token = ""
            st.rerun()
        
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
                "user": st.session_state.username
            }
            
            st.download_button(
                label="📄 Download Chat History",
                data=json.dumps(chat_data, indent=2),
                file_name=f"chat_history_{st.session_state.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
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
        
        try:
            with st.spinner("🤔 Processing your request..."):
                response = bedrock_agent_runtime.invoke_agent(
                    agent_id,
                    agent_alias_id,
                    st.session_state.session_id,
                    prompt
                )
            
            output_text = response["output_text"]
            
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
            st.error(f"❌ Error: {str(e)}")
            st.info("Please check your connection and try again.")

def main():
    st.set_page_config(
        page_title=ui_title,
        page_icon=ui_icon,
        layout="wide",
        initial_sidebar_state="collapsed" if not st.session_state.get('authenticated', False) else "expanded"
    )
    
    init_session_state()
    load_css()
    
    if st.session_state.authenticated:
        display_authenticated_app()
    else:
        cognito_login()

if __name__ == "__main__":
    main()