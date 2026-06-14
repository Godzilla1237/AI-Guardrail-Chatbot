import pandas as pd


def generate_report(metrics, avg_latency):

    report_data = {
        "Metric": [
            "Safe Messages",
            "Toxicity Blocks",
            "PII Blocks",
            "Prompt Injection Blocks",
            "Output Blocks",
            "Average Response Time (sec)"
        ],
        "Value": [
            metrics["safe_messages"],
            metrics["blocked_toxicity"],
            metrics["blocked_pii"],
            metrics["blocked_injection"],
            metrics["blocked_output"],
            avg_latency
        ]
    }

    return pd.DataFrame(report_data)