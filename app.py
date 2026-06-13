import streamlit as st
import re
from datetime import datetime
import pandas as pd
import os

st.set_page_config(page_title="AI Guardrail Chatbot", layout="centered")

LOG_FILE = "guardrail_logs.csv"

toxic_words = [
    "hate", "kill", "stupid", "idiot", "dumb", "hurt", "attack", "abuse"
]

prompt_injection_phrases = [
    "ignore previous instructions",
    "forget your instructions",
    "act as",
    "jailbreak",
    "bypass",
    "developer mode",
    "do anything now",
    "dan mode",
    "reveal your system prompt",
    "show hidden instructions"
]

def detect_toxicity(text):
    text_lower = text.lower()
    for word in toxic_words:
        if word in text_lower:
            return True, word
    return False, "None"

def detect_pii(text):
    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    phone_pattern = r"\b[6-9]\d{9}\b"
    aadhaar_pattern = r"\b\d{4}\s?\d{4}\s?\d{4}\b"

    if re.search(email_pattern, text):
        return True, "Email"
    if re.search(phone_pattern, text):
        return True, "Phone Number"
    if re.search(aadhaar_pattern, text):
        return True, "Aadhaar-like Number"
    return False, "None"

def detect_prompt_injection(text):
    text_lower = text.lower()
    for phrase in prompt_injection_phrases:
        if phrase in text_lower:
            return True, phrase
    return False, "None"

def save_log(user_input, category, reason):
    log_data = {
        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "User Input": user_input,
        "Category": category,
        "Reason": reason
    }

    df = pd.DataFrame([log_data])

    if os.path.exists(LOG_FILE):
        df.to_csv(LOG_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(LOG_FILE, index=False)

def chatbot_response(user_input):
    return f"You said: {user_input}"

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🤖 AI Guardrail Chatbot")
st.write("A safety-focused chatbot prototype with toxicity, PII, and prompt injection guardrails.")

page = st.sidebar.radio("Navigation", ["Chatbot", "Admin Dashboard", "About Project"])

if page == "Chatbot":
    st.subheader("Chat Interface")

    user_input = st.text_area("Enter your message")

    col1, col2 = st.columns(2)

    with col1:
        send_clicked = st.button("Send")

    with col2:
        clear_clicked = st.button("Clear Chat")

    if clear_clicked:
        st.session_state.messages = []
        st.success("Chat cleared.")

    if send_clicked:
        if user_input.strip() == "":
            st.warning("Please enter a message.")

        else:
            toxic, toxic_reason = detect_toxicity(user_input)
            pii, pii_reason = detect_pii(user_input)
            injection, injection_reason = detect_prompt_injection(user_input)

            if toxic:
                save_log(user_input, "Toxicity", toxic_reason)
                st.error(f"🚫 Message Blocked: Toxic content detected. Reason: {toxic_reason}")

            elif pii:
                save_log(user_input, "PII Detection", pii_reason)
                st.error(f"🚫 Message Blocked: Personal information detected. Reason: {pii_reason}")

            elif injection:
                save_log(user_input, "Prompt Injection", injection_reason)
                st.error(f"🚫 Message Blocked: Prompt injection attempt detected. Reason: {injection_reason}")

            else:
                response = chatbot_response(user_input)

                st.session_state.messages.append({
                    "user": user_input,
                    "bot": response
                })

                st.success("✅ Message Accepted")

    st.subheader("Conversation History")

    if len(st.session_state.messages) == 0:
        st.info("No conversation yet. Start by sending a safe message.")
    else:
        for chat in st.session_state.messages:
            st.markdown(f"**🧑 User:** {chat['user']}")
            st.markdown(f"**🤖 Bot:** {chat['bot']}")
            st.divider()

elif page == "Admin Dashboard":
    st.header("📊 Guardrail Logs Dashboard")

    if os.path.exists(LOG_FILE):
        logs = pd.read_csv(LOG_FILE)

        st.subheader("Flagged Messages")
        st.dataframe(logs, use_container_width=True)

        st.subheader("Category Count")
        st.bar_chart(logs["Category"].value_counts())

        st.subheader("Summary")
        st.write(f"Total flagged messages: {len(logs)}")

        most_common = logs["Category"].value_counts().idxmax()
        st.write(f"Most common violation: {most_common}")

    else:
        st.info("No unsafe messages logged yet.")

elif page == "About Project":
    st.header("ℹ️ About This Project")

    st.write("""
    This project is an AI chatbot prototype with multi-layer safety guardrails.

    The system checks user input before allowing it into the chatbot.

    Current guardrails:
    - Toxicity Detection
    - PII Detection
    - Prompt Injection Detection

    Current outputs:
    - Safe messages are accepted
    - Unsafe messages are blocked
    - Blocked messages are saved in logs
    - Admin dashboard displays flagged message statistics

    Future upgrades:
    - LLM API integration
    - Output guardrails
    - Indian language / Hinglish testing
    - Research evaluation metrics
    """)