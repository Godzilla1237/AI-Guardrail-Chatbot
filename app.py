import streamlit as st
from datetime import datetime
import pandas as pd
import os
from ollama import chat

from guardrails.pii import detect_pii
from guardrails.prompt_injection import detect_prompt_injection
from guardrails.output_guardrail import detect_harmful_output
from guardrails.metrics import metrics
from guardrails.performance import start_timer, end_timer
from guardrails.test_dataset import test_prompts
from guardrails.evaluator import evaluate_prompt
from guardrails.report_generator import generate_report
from guardrails.ai_toxicity import detect_ai_toxicity

st.set_page_config(
    page_title="AI Guardrail Chatbot",
    page_icon="🤖",
    layout="wide"
)

LOG_FILE = "guardrail_logs.csv"


st.markdown(
    """
    <style>
    .main {
        background-color: #0f1117;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1100px;
    }

    [data-testid="stSidebar"] {
        background-color: #171923;
    }

    [data-testid="stSidebar"] * {
        color: #f5f5f5;
    }

    .app-title {
        font-size: 34px;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 0px;
    }

    .app-subtitle {
        font-size: 15px;
        color: #a7a7a7;
        margin-bottom: 25px;
    }

    .chat-card {
        background-color: #171923;
        border: 1px solid #2d3748;
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 12px;
    }

    .user-bubble {
        background-color: #2d3748;
        color: #ffffff;
        padding: 14px 16px;
        border-radius: 16px 16px 4px 16px;
        margin: 10px 0px 8px auto;
        max-width: 78%;
        font-size: 15px;
        line-height: 1.5;
    }

    .bot-bubble {
        background-color: #1f2937;
        color: #f3f4f6;
        padding: 14px 16px;
        border-radius: 16px 16px 16px 4px;
        margin: 8px auto 12px 0px;
        max-width: 82%;
        font-size: 15px;
        line-height: 1.5;
        border-left: 4px solid #10a37f;
    }

    .small-caption {
        color: #9ca3af;
        font-size: 12px;
        margin-bottom: 8px;
    }

    .status-safe {
        background-color: rgba(16, 163, 127, 0.15);
        color: #34d399;
        padding: 8px 12px;
        border-radius: 999px;
        display: inline-block;
        font-size: 13px;
        font-weight: 600;
        margin-bottom: 10px;
    }

    .status-blocked {
        background-color: rgba(239, 68, 68, 0.15);
        color: #f87171;
        padding: 8px 12px;
        border-radius: 999px;
        display: inline-block;
        font-size: 13px;
        font-weight: 600;
        margin-bottom: 10px;
    }

    .metric-card {
        background-color: #171923;
        border: 1px solid #2d3748;
        border-radius: 14px;
        padding: 16px;
        text-align: center;
        margin-bottom: 12px;
    }

    .metric-number {
        color: #ffffff;
        font-size: 28px;
        font-weight: 800;
    }

    .metric-label {
        color: #9ca3af;
        font-size: 13px;
    }

    h1, h2, h3, h4, h5, h6, p, label, span, div {
        color: #f5f5f5;
    }

    .stTextArea textarea {
        background-color: #171923 !important;
        color: #ffffff !important;
        border: 1px solid #374151 !important;
        border-radius: 14px !important;
    }

    .stButton button {
        border-radius: 12px;
        font-weight: 700;
        padding: 0.5rem 1rem;
    }

    .stDataFrame {
        background-color: #171923;
    }
    </style>
    """,
    unsafe_allow_html=True
)


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


def get_average_latency():
    if "messages" not in st.session_state:
        return 0

    latencies = [
        msg["latency"]
        for msg in st.session_state.messages
        if "latency" in msg
    ]

    if not latencies:
        return 0

    return round(sum(latencies) / len(latencies), 2)


def metric_card(label, value):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-number">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_chat_history():
    if len(st.session_state.messages) == 0:
        st.info("No conversation yet. Start by sending a safe message.")
        return

    for chat_item in st.session_state.messages:
        st.markdown(
            f"""
            <div class="user-bubble">
                <b>You</b><br>{chat_item['user']}
            </div>
            """,
            unsafe_allow_html=True
        )

        latency_text = ""
        if "latency" in chat_item:
            latency_text = f"<div class='small-caption'>Response time: {chat_item['latency']} sec</div>"

        st.markdown(
            f"""
            <div class="bot-bubble">
                <b>Guarded AI</b><br>{chat_item['bot']}
            </div>
            {latency_text}
            """,
            unsafe_allow_html=True
        )


if "messages" not in st.session_state:
    st.session_state.messages = []

if "metrics" not in st.session_state:
    st.session_state.metrics = metrics.copy()

with st.sidebar:
    st.markdown("## 🛡️ Guardrail AI")
    st.caption("Local Llama 3.2 + Safety Layers")
    page = st.radio(
        "Navigation",
        [
            "💬 Chatbot",
            "📊 Admin Dashboard",
            "🧪 Evaluation",
            "📄 Report Generator",
            "ℹ️ About Project"
        ]
    )

    st.divider()

    st.markdown("### System Status")
    st.success("Llama 3.2 Connected")
    st.success("Input Guardrails Active")
    st.success("Output Guardrail Active")

    st.divider()

    if st.button("Reset Metrics"):
        st.session_state.metrics = metrics.copy()
        st.session_state.messages = []
        st.success("Metrics reset.")


st.markdown('<div class="app-title">AI Chatbot with Multi-Layer Safety Guardrails</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">A ChatGPT-style local AI assistant with toxicity, PII, prompt-injection, and output safety controls.</div>',
    unsafe_allow_html=True
)


if page == "💬 Chatbot":
    left_col, right_col = st.columns([2.2, 1])

    with left_col:
        st.markdown("### Chat")

        st.markdown('<div class="chat-card">', unsafe_allow_html=True)

        render_chat_history()

        st.markdown("</div>", unsafe_allow_html=True)

        user_input = st.text_area(
            "Message Guarded AI",
            placeholder="Ask something safe, for example: What is Artificial Intelligence?",
            height=120
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            send_clicked = st.button("Send Message", use_container_width=True)

        with col2:
            clear_clicked = st.button("Clear Chat", use_container_width=True)

        if clear_clicked:
            st.session_state.messages = []
            st.success("Chat cleared.")

        if send_clicked:
            if user_input.strip() == "":
                st.warning("Please enter a message.")

            else:
                with st.spinner("Running input guardrails..."):
                    toxic, toxic_reason, toxicity_score = detect_ai_toxicity(user_input)
                    pii, pii_reason = detect_pii(user_input)
                    injection, injection_reason = detect_prompt_injection(user_input)

                if toxic:
                    st.session_state.metrics["blocked_toxicity"] += 1
                    save_log(
                        user_input,
                        "Input Toxicity",
                        f"{toxic_reason} score={toxicity_score:.2f}"
                    )
                    st.markdown(
                        f"""
                        <div class="status-blocked">
                            🚫 Blocked by Toxicity Guardrail — {toxic_reason}, score {toxicity_score:.2f}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                elif pii:
                    st.session_state.metrics["blocked_pii"] += 1
                    save_log(user_input, "Input PII Detection", pii_reason)
                    st.markdown(
                        f"""
                        <div class="status-blocked">
                            🚫 Blocked by PII Guardrail — {pii_reason}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                elif injection:
                    st.session_state.metrics["blocked_injection"] += 1
                    save_log(user_input, "Input Prompt Injection", injection_reason)
                    st.markdown(
                        f"""
                        <div class="status-blocked">
                            🚫 Blocked by Prompt Injection Guardrail — {injection_reason}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                else:
                    with st.spinner("Generating safe AI response..."):
                        start = start_timer()
                        raw_response = chatbot_response(user_input)
                        latency = end_timer(start)

                    harmful_output, output_reason = detect_harmful_output(raw_response)

                    if harmful_output:
                        st.session_state.metrics["blocked_output"] += 1
                        save_log(raw_response, "Output Guardrail", output_reason)
                        final_response = "The model response was blocked by the output guardrail because it may contain unsafe content."

                    else:
                        st.session_state.metrics["safe_messages"] += 1
                        final_response = raw_response

                    st.session_state.messages.append({
                        "user": user_input,
                        "bot": final_response,
                        "latency": latency
                    })

                    st.markdown(
                        f"""
                        <div class="status-safe">
                            ✅ Input Passed Guardrails — Toxicity score {toxicity_score:.2f}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    st.rerun()

    with right_col:
        st.markdown("### Live Metrics")

        metric_card("Safe Messages", st.session_state.metrics["safe_messages"])
        metric_card("Toxicity Blocks", st.session_state.metrics["blocked_toxicity"])
        metric_card("PII Blocks", st.session_state.metrics["blocked_pii"])
        metric_card("Injection Blocks", st.session_state.metrics["blocked_injection"])
        metric_card("Output Blocks", st.session_state.metrics["blocked_output"])
        metric_card("Avg Response Time", f"{get_average_latency()} sec")


elif page == "📊 Admin Dashboard":
    st.markdown("### Admin Dashboard")

    col1, col2, col3 = st.columns(3)
    with col1:
        metric_card("Safe Messages", st.session_state.metrics["safe_messages"])
    with col2:
        metric_card("Toxicity Blocks", st.session_state.metrics["blocked_toxicity"])
    with col3:
        metric_card("PII Blocks", st.session_state.metrics["blocked_pii"])

    col4, col5, col6 = st.columns(3)
    with col4:
        metric_card("Prompt Injection Blocks", st.session_state.metrics["blocked_injection"])
    with col5:
        metric_card("Output Blocks", st.session_state.metrics["blocked_output"])
    with col6:
        metric_card("Average Response Time", f"{get_average_latency()} sec")

    st.divider()

    if os.path.exists(LOG_FILE):
        logs = pd.read_csv(LOG_FILE)

        st.markdown("### Flagged Messages")
        st.dataframe(logs, use_container_width=True)

        st.markdown("### Category Count")
        st.bar_chart(logs["Category"].value_counts())

        st.markdown("### Summary")
        st.write(f"Total flagged messages: {len(logs)}")

        most_common = logs["Category"].value_counts().idxmax()
        st.write(f"Most common violation: {most_common}")

    else:
        st.info("No unsafe messages logged yet.")


elif page == "🧪 Evaluation":
    st.markdown("### Guardrail Evaluation")

    st.write("Run automated tests on English and Hinglish prompts to check detection accuracy.")

    if st.button("Run Evaluation", use_container_width=True):
        correct = 0
        results = []

        for item in test_prompts:
            prompt = item["prompt"]
            expected = item["expected"]
            predicted = evaluate_prompt(prompt)

            status = "Correct" if predicted == expected else "Wrong"

            if predicted == expected:
                correct += 1

            results.append({
                "Prompt": prompt,
                "Expected": expected,
                "Predicted": predicted,
                "Status": status
            })

        total = len(test_prompts)
        accuracy = (correct / total) * 100

        col1, col2 = st.columns(2)
        with col1:
            metric_card("Detection Accuracy", f"{accuracy:.2f}%")
        with col2:
            metric_card("Correct Predictions", f"{correct}/{total}")

        results_df = pd.DataFrame(results)
        st.dataframe(results_df, use_container_width=True)

        csv_data = results_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download Evaluation Results CSV",
            data=csv_data,
            file_name="evaluation_results.csv",
            mime="text/csv",
            use_container_width=True
        )


elif page == "📄 Report Generator":
    st.markdown("### Guardrail Report Generator")

    avg_latency = get_average_latency()

    report_df = generate_report(
        st.session_state.metrics,
        avg_latency
    )

    st.dataframe(report_df, use_container_width=True)

    csv_report = report_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Guardrail Report CSV",
        data=csv_report,
        file_name="guardrail_report.csv",
        mime="text/csv",
        use_container_width=True
    )


elif page == "ℹ️ About Project":
    st.markdown("### About This Project")

    st.markdown(
        """
        This project is an AI chatbot prototype with multi-layer safety guardrails.

        **Architecture:**  
        User Input → Input Guardrails → Local Llama 3.2 Model → Output Guardrail → User Response

        **Current Guardrails**
        - ML-based Toxicity Detection using Detoxify
        - PII Detection using Microsoft Presidio
        - Prompt Injection Detection
        - Output Harmful Content Detection

        **Research Features**
        - Automated evaluation on English and Hinglish prompts
        - Detection accuracy calculation
        - CSV export
        - Latency tracking
        - Report generation

        **Future Work**
        - Larger adversarial dataset
        - Better Hinglish detection
        - False positive / false negative analysis
        - Paper-style experimental report
        """
    )