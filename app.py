import streamlit as st
from datetime import datetime
import pandas as pd
import os

from guardrails.toxicity import detect_toxicity
from guardrails.pii import detect_pii
from guardrails.prompt_injection import detect_prompt_injection
from guardrails.output_guardrail import detect_harmful_output

st.set_page_config(page_title="AI Guardrail Chatbot", layout="centered")

LOG_FILE = "guardrail_logs.csv"


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
    user_input_lower = user_input.lower()

    if "hello" in user_input_lower or "hi" in user_input_lower:
        return "Hello! I am a guarded AI chatbot prototype. How can I help you safely today?"

    elif "what is ai" in user_input_lower:
        return "AI stands for Artificial Intelligence. It allows machines to perform tasks that usually need human intelligence."

    elif "what is guardrail" in user_input_lower:
        return "A guardrail is a safety layer that checks user input and AI output to reduce harmful or unsafe responses."

    elif "project" in user_input_lower:
        return "This project demonstrates a multi-layer safety guardrail system for AI chatbots."

    elif "weapon" in user_input_lower or "hack" in user_input_lower:
        return "I cannot help with harmful, illegal, or unsafe activities."

    else:
        return f"I received your message safely: {user_input}"


if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🤖 AI Guardrail Chatbot")
st.write("A safety-focused chatbot prototype with input and output guardrails.")

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
                save_log(user_input, "Input Toxicity", toxic_reason)
                st.error(f"🚫 Input Blocked: Toxic content detected. Reason: {toxic_reason}")

            elif pii:
                save_log(user_input, "Input PII Detection", pii_reason)
                st.error(f"🚫 Input Blocked: Personal information detected. Reason: {pii_reason}")

            elif injection:
                save_log(user_input, "Input Prompt Injection", injection_reason)
                st.error(f"🚫 Input Blocked: Prompt injection attempt detected. Reason: {injection_reason}")

            else:
                raw_response = chatbot_response(user_input)

                harmful_output, output_reason = detect_harmful_output(raw_response)

                if harmful_output:
                    save_log(raw_response, "Output Guardrail", output_reason)
                    final_response = "⚠️ The chatbot response was blocked by the output guardrail because it may contain unsafe content."
                else:
                    final_response = raw_response

                st.session_state.messages.append({
                    "user": user_input,
                    "bot": final_response
                })

                st.success("✅ Input Passed Guardrails")

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

    The system checks user input before allowing it into the chatbot and also checks the chatbot's response before showing it to the user.

    Current guardrails:
    - Input Toxicity Detection
    - Input PII Detection
    - Input Prompt Injection Detection
    - Output Harmful Content Detection

    Current outputs:
    - Safe messages are accepted
    - Unsafe inputs are blocked
    - Unsafe outputs are blocked
    - Blocked messages are saved in logs
    - Admin dashboard displays flagged message statistics

    Future upgrades:
    - LLM API integration
    - HuggingFace toxicity model
    - Microsoft Presidio PII detection
    - Indian language / Hinglish testing
    - Research evaluation metrics
    """)