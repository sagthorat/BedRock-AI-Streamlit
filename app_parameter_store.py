import json
import logging
import re
from services import bedrock_agent_runtime
from config.parameter_store import get_app_config
import streamlit as st
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get config from Parameter Store
try:
    config = get_app_config()
    agent_id = config['agent_id']
    agent_alias_id = config['agent_alias_id']
    ui_title = config['ui_title']
    ui_icon = config['ui_icon']
    aws_region = config['aws_region']
    
    if not agent_id or not agent_alias_id:
        st.error("❌ Agent configuration not found. Please check Parameter Store or environment variables.")
        st.stop()
        
except Exception as e:
    st.error(f"❌ Configuration error: {str(e)}")
    st.stop()

# Custom CSS for modern styling
def load_css():
    st.markdown("""
    <style>
    :root {
        --primary-color: #1f77b4;
        --secondary-color: #ff7f0e;
        --success-color: #2ca02c;
        --warning-color: #d62728;
        --background-color: #f8f9fa;
        --card-background: #ffffff;
        --text-color: #2c3e50;
        --border-color: #e1e8ed;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    .chat-container {
        background: var(--card-background);
        border-radius: 15px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        border: 1px solid var(--border-color);
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px 15px 5px 15px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }
    
    .assistant-message {
        background: #f8f9fa;
        color: var(--text-color);
        padding: 1rem;
        border-radius: 15px 15px 15px 5px;
        margin: 0.5rem 0;
        border-left: 4px solid var(--primary-color);
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
    }
    
    .citation-badge {
        background: var(--primary-color);
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
        margin: 0.2rem;
        display: inline-block;
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

def display_header():
    st.markdown(f"""
    <div class="main-header">
        <h1>{ui_icon} {ui_title}</h1>
        <p>Powered by Amazon Bedrock AI • Configuration from Parameter Store</p>
    </div>
    """, unsafe_allow_html=True)

def display_metrics():
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💬 Messages", st.session_state.message_count)
    
    with col2:
        session_duration = datetime.now() - st.session_state.session_start_time
        minutes = int(session_duration.total_seconds() / 60)
        st.metric("⏱️ Session Time", f"{minutes}m")
    
    with col3:
        st.metric("📚 Citations", len(st.session_state.citations))
    
    with col4:
        status = "🟢 Online" if agent_id else "🔴 Offline"
        st.metric("🤖 Agent Status", status)

def display_welcome_message():
    if not st.session_state.messages:
        st.markdown("""
        <div class="chat-container">
            <div class="assistant-message">
                <h3>👋 Welcome! I'm your AI Assistant</h3>
                <p>Configuration loaded from AWS Systems Manager Parameter Store</p>
                <p><strong>How can I assist you today?</strong></p>
            </div>
        </div>
        """, unsafe_allow_html=True)

def display_chat_message(message, is_user=False):
    message_class = "user-message" if is_user else "assistant-message"
    icon = "👤" if is_user else "🤖"
    
    st.markdown(f"""
    <div class="chat-container">
        <div class="{message_class}">
            <strong>{icon} {'You' if is_user else 'AI Assistant'}</strong>
            <div style="margin-top: 0.5rem;">
                {message}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def format_citations(text, citations):
    if not citations:
        return text
    
    citation_num = 1
    formatted_text = re.sub(r"%\[(\d+)\]%", r"<sup>[\1]</sup>", text)
    
    if citations:
        citation_html = "<div style='margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e1e8ed;'>"
        citation_html += "<h4>📚 Sources:</h4>"
        
        for citation in citations:
            for retrieved_ref in citation["retrievedReferences"]:
                citation_html += f"""
                <div class="citation-badge">
                    [{citation_num}] {retrieved_ref['location']['s3Location']['uri']}
                </div>
                """
                citation_num += 1
        citation_html += "</div>"
        formatted_text += citation_html
    
    return formatted_text

def display_sidebar():
    with st.sidebar:
        st.markdown("### 🎛️ Control Panel")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 New Chat", use_container_width=True):
                init_session_state()
                st.rerun()
        
        with col2:
            if st.button("📥 Export", use_container_width=True):
                if st.session_state.messages:
                    chat_data = {
                        "session_id": st.session_state.session_id,
                        "timestamp": datetime.now().isoformat(),
                        "messages": st.session_state.messages
                    }
                    st.download_button(
                        "💾 Download",
                        json.dumps(chat_data, indent=2),
                        f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        "application/json"
                    )
        
        st.markdown("---")
        
        st.markdown("### 🤖 Configuration")
        st.info(f"""
        **Agent ID:** `{agent_id[:8]}...`  
        **Session:** `{st.session_state.session_id[:8]}...`  
        **Region:** `{aws_region}`  
        **Source:** Parameter Store
        """)

def main():
    st.set_page_config(
        page_title=ui_title,
        page_icon=ui_icon,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    load_css()
    init_session_state()
    
    display_header()
    display_metrics()
    
    chat_container = st.container()
    
    with chat_container:
        display_welcome_message()
        
        for message in st.session_state.messages:
            if message["role"] == "user":
                display_chat_message(message["content"], is_user=True)
            else:
                formatted_content = format_citations(message["content"], st.session_state.citations)
                display_chat_message(formatted_content, is_user=False)
    
    if prompt := st.chat_input("💬 Type your message here...", key="chat_input"):
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
            
            formatted_content = format_citations(output_text, response["citations"])
            display_chat_message(formatted_content, is_user=False)
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    display_sidebar()

if __name__ == "__main__":
    main()