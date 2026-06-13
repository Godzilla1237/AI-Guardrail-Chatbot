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
    "dan mode"
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

st.title("🤖 AI Guardrail Chatbot")
st.write("This chatbot checks user input using safety guardrails before accepting it.")

page = st.sidebar.radio("Navigation", ["Chatbot", "Admin Dashboard"])

if page == "Chatbot":
    user_input = st.text_area("Enter your message")

    if st.button("Send"):
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
                st.success("✅ Message Accepted")
                st.write("Bot Response:")
                st.info("This is a safe response from the chatbot. In the final version, this will connect to an LLM API.")

elif page == "Admin Dashboard":
    st.header("📊 Guardrail Logs Dashboard")

    if os.path.exists(LOG_FILE):
        logs = pd.read_csv(LOG_FILE)

        st.subheader("Flagged Messages")
        st.dataframe(logs)

        st.subheader("Category Count")
        st.bar_chart(logs["Category"].value_counts())

    else:
        st.info("No unsafe messages logged yet.")