import streamlit as st
from agent import get_financial_advice, reset_conversation

COUNTRIES = ["United States", "India", "Bahrain", "Qatar", "UAE", "Saudi Arabia", "Kuwait", "Oman"]

# App title
st.set_page_config(page_title="Neurasix Financial Advisor", layout="wide")
st.title("🤖 Neurasix Financial Advisor Chatbot")

# Initialize session state for conversation
if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_confidence" not in st.session_state:
    st.session_state.show_confidence = False
if "last_confidence" not in st.session_state:
    st.session_state.last_confidence = 0

# Sidebar for reset
with st.sidebar:
    st.header("🔧 Settings")
    if st.button("Reset Conversation"):
        reset_conversation()
        st.session_state.messages = []
        st.success("Conversation has been reset.")

    # Inside the sidebar settings
    st.header("🌍 Select Country")
    selected_country = st.selectbox("Choose your country", COUNTRIES)
    st.session_state.selected_country = selected_country

# Chat tabs: Main response and confidence score
tab1, tab2 = st.tabs(["💬 Chat", "📊 Confidence Score"])

with tab1:
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input box for user prompt
    user_input = st.chat_input("Ask...")

    if user_input:
        # Show user's message
        st.chat_message("user").markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Get AI response
        response = get_financial_advice(user_input, selected_country)
        reply_text = response.get("response", "I'm sorry, I couldn't understand that.")
        confidence = response.get("confidence", 50)

        # Show AI's response
        st.chat_message("assistant").markdown(reply_text)
        st.session_state.messages.append({"role": "assistant", "content": reply_text})

        # Store confidence
        st.session_state.last_confidence = confidence
        st.session_state.show_confidence = True

with tab2:
    st.subheader("🧠 Confidence Score")
    if st.session_state.show_confidence:
        st.metric(label="Model Confidence", value=f"{st.session_state.last_confidence}%")
    else:
        st.info("Ask a question in the Chat tab to see the confidence score here.")
