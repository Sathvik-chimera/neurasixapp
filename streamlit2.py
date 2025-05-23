import streamlit as st
from claude_agent import get_financial_advice as get_claude_advice, reset_conversation as reset_claude
from chatgpt_agent import get_financial_advice as get_chatgpt_advice, reset_conversation as reset_chatgpt

COUNTRIES = ["United States", "India", "Bahrain", "Qatar", "UAE", "Saudi Arabia", "Kuwait", "Oman"]
MODELS = ["Claude 3.5", "ChatGPT 4"]

st.set_page_config(page_title="Neurasix Financial Advisor", layout="wide")
st.title("🤖 Neurasix Financial Advisor Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_confidence" not in st.session_state:
    st.session_state.last_confidence = 0
if "selected_model" not in st.session_state:
    st.session_state.selected_model = MODELS[0]

with st.sidebar:
    st.header("🔧 Settings")
    if st.button("Reset Conversation"):
        if st.session_state.selected_model == "Claude 3.5":
            reset_claude()
        else:
            reset_chatgpt()
        st.session_state.messages = []
        st.success("Conversation reset.")

    st.header("🌍 Select Country")
    selected_country = st.selectbox("Choose your country", COUNTRIES)
    st.session_state.selected_country = selected_country

    st.header("🧠 Choose Model")
    selected_model = st.selectbox("Model", MODELS)
    st.session_state.selected_model = selected_model

tab1, tab2 = st.tabs(["💬 Chat", "📊 Confidence Score"])

with tab1:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask...")
    if user_input:
        st.chat_message("user").markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        if selected_model == "Claude 3.5":
            response = get_claude_advice(user_input, selected_country)
        else:
            response = get_chatgpt_advice(user_input, selected_country)

        reply = response.get("response", "Sorry, I couldn't process that.")
        conf = response.get("confidence", 50)

        st.chat_message("assistant").markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.session_state.last_confidence = conf

with tab2:
    st.subheader("🧠 Confidence Score")
    if st.session_state.messages:
        st.metric("Model Confidence", f"{st.session_state.last_confidence}%")
    else:
        st.info("Ask something to see the confidence score.")
