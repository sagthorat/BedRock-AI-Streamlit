from dotenv import load_dotenv
import json
import logging
import logging.config
import os
import re
from services import bedrock_agent_runtime
import streamlit as st
import uuid
import yaml
from datetime import datetime
import time

# Load environment variables
load_dotenv()

# Get config from environment variables
agent_id = os.getenv('BEDROCK_AGENT_ID')
agent_alias_id = os.getenv('BEDROCK_AGENT_ALIAS_ID')
ui_title = os.getenv('BEDROCK_AGENT_TEST_UI_TITLE', 'Welcome to CenITex Modern Cloud Cost Calculator Powered by AI')
ui_icon = os.getenv('BEDROCK_AGENT_TEST_UI_ICON', '🤖')
logo_path = os.getenv('BEDROCK_AGENT_TEST_UI_LOGO', 'logo.png')

# Simple CSS styling
def load_css():
    st.markdown("""
    <style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Simple header */
    .main-header {
        background: #1f77b4;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        text-align: center;
        color: white;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2rem;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
    }
    
    /* Simple message styling */
    .user-message {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    
    .assistant-message {
        background: #f5f5f5;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #666;
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
    # Display logo if it exists
    if os.path.exists(logo_path):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(logo_path, width=200)
    
    st.markdown(f"""
    <div class="main-header">
        <h1>{ui_icon} {ui_title}</h1>
        <p>Calculate Hosting costs based on Support Type and Cloud Consumption</p>
    </div>
    """, unsafe_allow_html=True)

def display_metrics():
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💬 Messages",
            value=st.session_state.message_count,
            delta=None
        )
    
    with col2:
        session_duration = datetime.now() - st.session_state.session_start_time
        minutes = int(session_duration.total_seconds() / 60)
        st.metric(
            label="⏱️ Session Time",
            value=f"{minutes}m",
            delta=None
        )
    
    with col3:
        st.metric(
            label="📚 Citations",
            value=len(st.session_state.citations),
            delta=None
        )
    
    with col4:
        status = "🟢 Online" if agent_id else "🔴 Offline"
        st.metric(
            label="🤖 Agent Status",
            value=status,
            delta=None
        )

def display_welcome_message():
    if not st.session_state.messages:
        st.markdown("""
        <div class="assistant-message">
            <h3>Welcome! I'm your AI Cost Calculator</h3>
            <p>I'm here to help you with your costing related questions on CenITex Modern Cloud</p>                
            <p><strong>How can I assist you today?</strong></p>
        </div>
        """, unsafe_allow_html=True)

def display_chat_message(message, is_user=False):
    message_class = "user-message" if is_user else "assistant-message"
    icon = "👤" if is_user else "🤖"
    
    st.markdown(f"""
    <div class="{message_class}">
        <strong>{icon} {'You' if is_user else 'AI Assistant'}</strong>
        <div style="margin-top: 0.5rem;">
            {message}
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_typing_indicator():
    st.markdown("""
    <div class="assistant-message">
        <strong>🤖 AI Assistant</strong>
        <div style="margin-top: 0.5rem;">
            <em>Thinking...</em> ⏳
        </div>
    </div>
    """, unsafe_allow_html=True)

def format_citations(text, citations):
    if not citations:
        return text
    
    # Replace citation markers with styled badges
    citation_num = 1
    formatted_text = re.sub(r"%\[(\d+)\]%", r"<sup>[\1]</sup>", text)
    
    # Add citation sources at the end
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
        
        # Session controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 New Chat", use_container_width=True):
                init_session_state()
                st.rerun()
        
        with col2:
            if st.button("📥 Export", use_container_width=True):
                export_chat()
        
        st.markdown("---")
        
        # # Agent information
        # st.markdown("### 🤖 Agent Info")
        # st.info(f"""
        # **Agent ID:** `{agent_id[:8]}...`  
        # **Session:** `{st.session_state.session_id[:8]}...`  
        # **Region:** `{os.getenv('AWS_DEFAULT_REGION', 'us-east-1')}`
        # """)
        
        # Advanced options
        # with st.expander("⚙️ Advanced Options"):
        #     show_trace = st.checkbox("Show Trace Data", value=False)
        #     show_citations = st.checkbox("Show Citations", value=True)
        #     debug_mode = st.checkbox("Debug Mode", value=False)
        
        # # Display trace information if enabled
        # if show_trace and st.session_state.trace:
        #     display_trace_sidebar()
        
        # # Display citations if enabled
        # if show_citations and st.session_state.citations:
        #     display_citations_sidebar()

# def display_trace_sidebar():
#     st.markdown("### 🔍 Trace Information")
    
#     trace_types_map = {
#         "Pre-Processing": ["preGuardrailTrace", "preProcessingTrace"],
#         "Orchestration": ["orchestrationTrace"],
#         "Post-Processing": ["postProcessingTrace", "postGuardrailTrace"]
#     }
    
#     step_num = 1
#     for trace_type_header in trace_types_map:
#         with st.expander(f"📋 {trace_type_header}", expanded=False):
#             has_trace = False
#             for trace_type in trace_types_map[trace_type_header]:
#                 if trace_type in st.session_state.trace:
#                     has_trace = True
#                     st.json(st.session_state.trace[trace_type])
#                     step_num += 1
#             if not has_trace:
#                 st.text("No trace data available")

# def display_citations_sidebar():
#     st.markdown("### 📚 Citations")
    
#     if st.session_state.citations:
#         citation_num = 1
#         for citation in st.session_state.citations:
#             for retrieved_ref in citation["retrievedReferences"]:
#                 with st.expander(f"📄 Citation [{citation_num}]", expanded=False):
#                     st.json({
#                         "generatedResponsePart": citation["generatedResponsePart"],
#                         "retrievedReference": retrieved_ref
#                     })
#                 citation_num += 1
#     else:
#         st.text("No citations available")

def export_chat():
    if st.session_state.messages:
        chat_data = {
            "session_id": st.session_state.session_id,
            "timestamp": datetime.now().isoformat(),
            "messages": st.session_state.messages,
            "message_count": st.session_state.message_count
        }
        
        st.download_button(
            label="💾 Download Chat History",
            data=json.dumps(chat_data, indent=2),
            file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

def main():
    # Page configuration
    st.set_page_config(
        page_title=ui_title,
        page_icon=ui_icon,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load custom CSS
    load_css()
    
    # Initialize session state
    init_session_state()
    
    # Display header
    display_header()
    
    # Display metrics
    display_metrics()
    
    # Main chat area
    chat_container = st.container()
    
    with chat_container:
        # Display welcome message if no conversation
        display_welcome_message()
        
        # Display conversation history
        for message in st.session_state.messages:
            if message["role"] == "user":
                display_chat_message(message["content"], is_user=True)
            else:
                formatted_content = format_citations(message["content"], st.session_state.citations)
                display_chat_message(formatted_content, is_user=False)
    
    # Chat input
    if prompt := st.chat_input("💬 Type your message here...", key="chat_input"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.message_count += 1
        
        # Display user message
        display_chat_message(prompt, is_user=True)
        
        # Show typing indicator
        typing_placeholder = st.empty()
        with typing_placeholder:
            display_typing_indicator()
        
        try:
            # Get AI response
            with st.spinner("🤔 Processing your request..."):
                response = bedrock_agent_runtime.invoke_agent(
                    agent_id,
                    agent_alias_id,
                    st.session_state.session_id,
                    prompt
                )
            
            # Clear typing indicator
            typing_placeholder.empty()
            
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
            formatted_content = format_citations(output_text, response["citations"])
            display_chat_message(formatted_content, is_user=False)
            
        except Exception as e:
            typing_placeholder.empty()
            st.error(f"❌ Error: {str(e)}")
            st.info("Please check your connection and try again.")
    
    # Display sidebar
    display_sidebar()

if __name__ == "__main__":
    main()