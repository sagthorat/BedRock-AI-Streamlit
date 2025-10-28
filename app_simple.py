from dotenv import load_dotenv
import json
import os
from services import bedrock_agent_runtime
import streamlit as st
import uuid
from datetime import datetime

# Load environment variables
load_dotenv()

# Get config from environment variables
agent_id = os.getenv('BEDROCK_AGENT_ID')
agent_alias_id = os.getenv('BEDROCK_AGENT_ALIAS_ID')
ui_title = os.getenv('BEDROCK_AGENT_TEST_UI_TITLE', 'Welcome to CenITex Modern Cloud Cost Calculator Powered by AI')
ui_icon = os.getenv('BEDROCK_AGENT_TEST_UI_ICON', '🤖')

# Custom CSS styling
def load_css():
    st.markdown("""
    <style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Global background - purple theme */
    .stApp {
        background: linear-gradient(135deg, #e8e3f0 0%, #d4c5e8 100%);
    }
    
    /* Header styling */
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
    
    /* Message styling */
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
    
    /* Enhanced input box styling - bigger and higher */
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
    
    /* Ensure main content doesn't overlap with sidebar */
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

def main():
    # Page configuration
    st.set_page_config(
        page_title=ui_title,
        page_icon=ui_icon,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    init_session_state()
    
    # Load CSS
    load_css()
    
    # SIDEBAR - Using with statement for better compatibility
    with st.sidebar:
        # Logo at the top if it exists
        if os.path.exists("logo.png"):
            st.image("logo.png", width=200)
            st.divider()
        
        st.title("🎛️ Control Panel")
        
        # Agent Status
        st.subheader("🤖 Agent Status")
        status = "🟢 Online" if agent_id else "🔴 Offline"
        st.success(f"Status: {status}")
        st.info(f"Messages: {st.session_state.message_count}")
        
        st.divider()
        
        # Session Controls
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
        
        # Download Options
        st.subheader("Save a copy of chat history?")
        if st.session_state.messages:
            chat_data = {
                "session_id": st.session_state.session_id,
                "timestamp": datetime.now().isoformat(),
                "messages": st.session_state.messages,
                "message_count": st.session_state.message_count
            }
            
            st.download_button(
                label="📄 Download Chat History",
                data=json.dumps(chat_data, indent=2),
                file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        else:
            st.info("No chat history available")
    
    # MAIN CONTENT
    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1>{ui_icon} {ui_title}</h1>
        <p>Calculate Hosting costs based on Support Type and Cloud Consumption</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Chat messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            display_chat_message(message["content"], is_user=True)
        else:
            display_chat_message(message["content"], is_user=False)
    
    # Add spacer to prevent input box overlap
    st.markdown("<div style='height: 300px;'></div>", unsafe_allow_html=True)
    
    # Chat input
    if prompt := st.chat_input("Please start by typing preferred cloud platform, support type and estimated consumption costs"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.message_count += 1
        
        # Display user message
        display_chat_message(prompt, is_user=True)
        
        try:
            # Get AI response
            with st.spinner("🤔 Processing your request..."):
                response = bedrock_agent_runtime.invoke_agent(
                    agent_id,
                    agent_alias_id,
                    st.session_state.session_id,
                    prompt
                )
            
            # Process response
            output_text = response["output_text"]
            
            # Handle JSON responses
            try:
                output_json = json.loads(output_text, strict=False)
                if "instruction" in output_json and "result" in output_json:
                    output_text = output_json["result"]
            except json.JSONDecodeError:
                pass
            
            # Store response data
            st.session_state.messages.append({"role": "assistant", "content": output_text})
            st.session_state.citations = response["citations"]
            st.session_state.trace = response["trace"]
            
            # Display AI response
            display_chat_message(output_text, is_user=False)
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("Please check your connection and try again.")

if __name__ == "__main__":
    main()