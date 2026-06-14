from guardrails.ai_toxicity import detect_ai_toxicity
from guardrails.pii import detect_pii
from guardrails.prompt_injection import detect_prompt_injection


def evaluate_prompt(prompt):
    toxic, _, _ = detect_ai_toxicity(prompt)
    if toxic:
        return "toxicity"

    pii, _ = detect_pii(prompt)
    if pii:
        return "pii"

    injection, _ = detect_prompt_injection(prompt)
    if injection:
        return "injection"

    return "safe"