import streamlit as st
from datetime import datetime
import pandas as pd
import os
from ollama import chat

from guardrails.toxicity import detect_toxicity
from guardrails.pii import detect_pii
from guardrails.prompt_injection import detect_prompt_injection
from guardrails.output_guardrail import detect_harmful_output
from guardrails.metrics import metrics
from guardrails.performance import start_timer, end_timer

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
    try:
        response = chat(
            model="llama3.2",
            messages=[
                {
                    "role": "system",
                    "content": """
                    You are a helpful AI assistant.
                    Give safe, simple, educational answers.
                    Do not provide harmful, illegal, or unsafe instructions.
                    Keep responses short and clear.
                    """
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ]
        )

        return response["message"]["content"]

    except Exception as e:
        return f"Model Error: {str(e)}"


if "messages" not in st.session_state:
    st.session_state.messages = []

if "metrics" not in st.session_state:
    st.session_state.metrics = metrics.copy()

st.title("🤖 AI Guardrail Chatbot")
st.write("A safety-focused chatbot prototype using local Llama 3.2 with input and output guardrails.")

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
                st.session_state.metrics["blocked_toxicity"] += 1
                save_log(user_input, "Input Toxicity", toxic_reason)
                st.error(f"🚫 Input Blocked: Toxic content detected. Reason: {toxic_reason}")

            elif pii:
                st.session_state.metrics["blocked_pii"] += 1
                save_log(user_input, "Input PII Detection", pii_reason)
                st.error(f"🚫 Input Blocked: Personal information detected. Reason: {pii_reason}")

            elif injection:
                st.session_state.metrics["blocked_injection"] += 1
                save_log(user_input, "Input Prompt Injection", injection_reason)
                st.error(f"🚫 Input Blocked: Prompt injection attempt detected. Reason: {injection_reason}")

            else:
                with st.spinner("Generating safe AI response..."):
                    start = start_timer()
                    raw_response = chatbot_response(user_input)
                    latency = end_timer(start)

                harmful_output, output_reason = detect_harmful_output(raw_response)

                if harmful_output:
                    st.session_state.metrics["blocked_output"] += 1
                    save_log(raw_response, "Output Guardrail", output_reason)
                    final_response = "⚠️ The chatbot response was blocked by the output guardrail because it may contain unsafe content."

                else:
                    st.session_state.metrics["safe_messages"] += 1
                    final_response = raw_response

                st.session_state.messages.append({
                    "user": user_input,
                    "bot": final_response,
                    "latency": latency
                })

                st.success("✅ Input Passed Guardrails")

    st.subheader("Conversation History")

    if len(st.session_state.messages) == 0:
        st.info("No conversation yet. Start by sending a safe message.")
    else:
        for chat_item in st.session_state.messages:
            st.markdown(f"**🧑 User:** {chat_item['user']}")
            st.markdown(f"**🤖 Bot:** {chat_item['bot']}")

            if "latency" in chat_item:
                st.caption(f"Response Time: {chat_item['latency']} sec")

            st.divider()


elif page == "Admin Dashboard":
    st.header("📊 Guardrail Logs Dashboard")

    st.subheader("Live Evaluation Metrics")

    col1, col2, col3 = st.columns(3)

    col1.metric("Safe Messages", st.session_state.metrics["safe_messages"])
    col2.metric("Toxicity Blocks", st.session_state.metrics["blocked_toxicity"])
    col3.metric("PII Blocks", st.session_state.metrics["blocked_pii"])

    col4, col5 = st.columns(2)

    col4.metric("Prompt Injection Blocks", st.session_state.metrics["blocked_injection"])
    col5.metric("Output Blocks", st.session_state.metrics["blocked_output"])

    if st.session_state.messages:
        latencies = [
            msg["latency"]
            for msg in st.session_state.messages
            if "latency" in msg
        ]

        if latencies:
            avg_latency = round(sum(latencies) / len(latencies), 2)
            st.metric("Average Response Time", f"{avg_latency} sec")

    st.divider()

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

    The system checks user input before sending it to a local LLM and also checks the model's response before showing it to the user.

    Current architecture:
    User Input → Input Guardrails → Local Llama 3.2 Model → Output Guardrail → User Response

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
    - Live evaluation metrics are displayed
    - Response latency is measured

    Future upgrades:
    - HuggingFace toxicity model
    - Microsoft Presidio PII detection
    - Indian language / Hinglish testing
    - Accuracy, precision, recall and false positive evaluation
    - Research paper-style experiment results
    """)