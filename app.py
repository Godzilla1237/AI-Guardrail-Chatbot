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
        background: linear-gradient(135deg, #0f1117 0%, #111827 45%, #0b1120 100%);
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1150px;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111827 0%, #0f172a 100%);
        border-right: 1px solid #263244;
    }

    [data-testid="stSidebar"] * {
        color: #f5f5f5;
    }

    section[data-testid="stSidebar"] div.stButton > button {
        width: 100%;
        height: 52px;
        border-radius: 15px;
        border: 1px solid #293548;
        background: rgba(31, 41, 55, 0.62);
        color: #e5e7eb;
        font-size: 15px;
        font-weight: 700;
        text-align: left;
        padding-left: 18px;
        transition: all 0.25s ease-in-out;
    }

    section[data-testid="stSidebar"] div.stButton > button:hover {
        background: rgba(16, 163, 127, 0.16);
        border: 1px solid #10a37f;
        color: #ffffff;
        transform: translateX(5px);
        box-shadow: 0 8px 24px rgba(16, 163, 127, 0.15);
    }

    .nav-active {
        background: linear-gradient(135deg, rgba(16, 163, 127, 0.35), rgba(34, 197, 94, 0.16));
        border: 1px solid #10a37f;
        border-radius: 15px;
        padding: 14px 18px;
        margin-bottom: 10px;
        font-size: 15px;
        font-weight: 800;
        color: #ffffff;
        box-shadow: 0 10px 30px rgba(16, 163, 127, 0.22);
    }

    .sidebar-logo {
        background: radial-gradient(circle at top left, rgba(16, 163, 127, 0.32), rgba(31, 41, 55, 0.92));
        border: 1px solid #263244;
        border-radius: 22px;
        padding: 18px;
        margin-bottom: 18px;
        box-shadow: 0 12px 35px rgba(0,0,0,0.25);
    }

    .sidebar-title {
        font-size: 24px;
        font-weight: 900;
        color: #ffffff;
        margin-bottom: 4px;
    }

    .sidebar-subtitle {
        font-size: 13px;
        color: #9ca3af;
    }

    .status-pill {
        background: rgba(16, 163, 127, 0.13);
        color: #34d399;
        border: 1px solid rgba(16, 163, 127, 0.35);
        border-radius: 999px;
        padding: 8px 11px;
        font-size: 12px;
        font-weight: 700;
        display: inline-block;
        margin: 4px 3px 4px 0;
    }

    .app-title {
        font-size: 36px;
        font-weight: 900;
        color: #ffffff;
        margin-bottom: 0px;
        letter-spacing: -0.5px;
    }

    .app-subtitle {
        font-size: 15px;
        color: #a7a7a7;
        margin-bottom: 25px;
    }

    .user-bubble {
        background: linear-gradient(135deg, #374151, #2d3748);
        color: #ffffff;
        padding: 14px 16px;
        border-radius: 16px 16px 4px 16px;
        margin: 10px 0px 8px auto;
        max-width: 78%;
        font-size: 15px;
        line-height: 1.5;
        box-shadow: 0 8px 24px rgba(0,0,0,0.18);
    }

    .bot-bubble {
        background: linear-gradient(135deg, #1f2937, #172033);
        color: #f3f4f6;
        padding: 14px 16px;
        border-radius: 16px 16px 16px 4px;
        margin: 8px auto 12px 0px;
        max-width: 82%;
        font-size: 15px;
        line-height: 1.5;
        border-left: 4px solid #10a37f;
        box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    }

    .small-caption {
        color: #9ca3af;
        font-size: 12px;
        margin-bottom: 8px;
    }

    .status-safe {
        background: rgba(16, 163, 127, 0.15);
        color: #34d399;
        padding: 9px 13px;
        border-radius: 999px;
        display: inline-block;
        font-size: 13px;
        font-weight: 700;
        margin-bottom: 10px;
        border: 1px solid rgba(16, 163, 127, 0.35);
    }

    .status-blocked {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        padding: 9px 13px;
        border-radius: 999px;
        display: inline-block;
        font-size: 13px;
        font-weight: 700;
        margin-bottom: 10px;
        border: 1px solid rgba(239, 68, 68, 0.35);
    }

    .metric-card {
        background: rgba(23, 25, 35, 0.88);
        border: 1px solid #2d3748;
        border-radius: 16px;
        padding: 17px;
        text-align: center;
        margin-bottom: 12px;
        transition: all 0.25s ease-in-out;
        box-shadow: 0 12px 28px rgba(0,0,0,0.18);
    }

    .metric-card:hover {
        transform: translateY(-3px);
        border-color: #10a37f;
        box-shadow: 0 14px 36px rgba(16, 163, 127, 0.14);
    }

    .metric-number {
        color: #ffffff;
        font-size: 29px;
        font-weight: 900;
    }

    .metric-label {
        color: #9ca3af;
        font-size: 13px;
        margin-top: 4px;
    }

    h1, h2, h3, h4, h5, h6, p, label, span, div {
        color: #f5f5f5;
    }

    .stButton button {
        border-radius: 13px;
        font-weight: 800;
        padding: 0.55rem 1rem;
        transition: all 0.2s ease-in-out;
    }

    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 10px 24px rgba(16, 163, 127, 0.16);
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


def switch_page(page_name):
    st.session_state.current_page = page_name
    st.rerun()


def nav_button(label, page_key):
    if st.session_state.current_page == page_key:
        st.markdown(
            f"""
            <div class="nav-active">
                {label}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        if st.button(label, key=f"nav_{page_key}", use_container_width=True):
            switch_page(page_key)


def process_user_message(user_input):
    if user_input.strip() == "":
        st.warning("Please enter a message.")
        return

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
        st.session_state.last_status = (
            "blocked",
            f"🚫 Blocked by Toxicity Guardrail — {toxic_reason}, score {toxicity_score:.2f}"
        )
        return

    if pii:
        st.session_state.metrics["blocked_pii"] += 1
        save_log(user_input, "Input PII Detection", pii_reason)
        st.session_state.last_status = (
            "blocked",
            f"🚫 Blocked by PII Guardrail — {pii_reason}"
        )
        return

    if injection:
        st.session_state.metrics["blocked_injection"] += 1
        save_log(user_input, "Input Prompt Injection", injection_reason)
        st.session_state.last_status = (
            "blocked",
            f"🚫 Blocked by Prompt Injection Guardrail — {injection_reason}"
        )
        return

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

    st.session_state.last_status = (
        "safe",
        f"✅ Input Passed Guardrails — Toxicity score {toxicity_score:.2f}"
    )


if "messages" not in st.session_state:
    st.session_state.messages = []

if "metrics" not in st.session_state:
    st.session_state.metrics = metrics.copy()

if "current_page" not in st.session_state:
    st.session_state.current_page = "chatbot"

if "last_status" not in st.session_state:
    st.session_state.last_status = None


with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-logo">
            <div class="sidebar-title">🛡️ Guardrail AI</div>
            <div class="sidebar-subtitle">Local Llama 3.2 + Safety Layers</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    nav_button("💬  Chatbot", "chatbot")
    nav_button("📊  Admin Dashboard", "dashboard")
    nav_button("🧪  Evaluation", "evaluation")
    nav_button("📄  Report Generator", "report")
    nav_button("ℹ️  About Project", "about")

    st.divider()

    st.markdown("### System Status")
    st.markdown('<span class="status-pill">● Llama 3.2 Connected</span>', unsafe_allow_html=True)
    st.markdown('<span class="status-pill">● Input Guardrails Active</span>', unsafe_allow_html=True)
    st.markdown('<span class="status-pill">● Output Guardrail Active</span>', unsafe_allow_html=True)

    st.divider()

    if st.button("🔄 Reset Session", use_container_width=True):
        st.session_state.metrics = metrics.copy()
        st.session_state.messages = []
        st.session_state.current_page = "chatbot"
        st.session_state.last_status = None
        st.success("Session reset.")


st.markdown('<div class="app-title">AI Chatbot with Multi-Layer Safety Guardrails</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">A ChatGPT-style local AI assistant with toxicity, PII, prompt-injection, and output safety controls.</div>',
    unsafe_allow_html=True
)

page = st.session_state.current_page


if page == "chatbot":
    left_col, right_col = st.columns([2.2, 1])

    with left_col:
        st.markdown("### Chat")

        if st.session_state.last_status:
            status_type, status_message = st.session_state.last_status

            if status_type == "safe":
                st.markdown(
                    f'<div class="status-safe">{status_message}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="status-blocked">{status_message}</div>',
                    unsafe_allow_html=True
                )

        render_chat_history()

        prompt = st.chat_input("Message Guarded AI...")

        if prompt:
            process_user_message(prompt)
            st.rerun()

        if st.button("🧹 Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.last_status = None
            st.rerun()

    with right_col:
        st.markdown("### Live Metrics")

        metric_card("Safe Messages", st.session_state.metrics["safe_messages"])
        metric_card("Toxicity Blocks", st.session_state.metrics["blocked_toxicity"])
        metric_card("PII Blocks", st.session_state.metrics["blocked_pii"])
        metric_card("Injection Blocks", st.session_state.metrics["blocked_injection"])
        metric_card("Output Blocks", st.session_state.metrics["blocked_output"])
        metric_card("Avg Response Time", f"{get_average_latency()} sec")


elif page == "dashboard":
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


elif page == "evaluation":
    st.markdown("### Guardrail Evaluation")

    st.write("Run automated tests on English and Hinglish prompts to check detection accuracy.")

    if st.button("🧪 Run Evaluation", use_container_width=True):
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
            label="⬇️ Download Evaluation Results CSV",
            data=csv_data,
            file_name="evaluation_results.csv",
            mime="text/csv",
            use_container_width=True
        )


elif page == "report":
    st.markdown("### Guardrail Report Generator")

    avg_latency = get_average_latency()

    report_df = generate_report(
        st.session_state.metrics,
        avg_latency
    )

    st.dataframe(report_df, use_container_width=True)

    csv_report = report_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇️ Download Guardrail Report CSV",
        data=csv_report,
        file_name="guardrail_report.csv",
        mime="text/csv",
        use_container_width=True
    )


elif page == "about":
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