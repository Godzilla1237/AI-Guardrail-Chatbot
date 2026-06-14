from guardrails.prompt_injection import detect_prompt_injection
from guardrails.ai_toxicity import detect_ai_toxicity
from guardrails.pii import detect_pii


def evaluate_prompt(prompt):

    injection, _ = detect_prompt_injection(prompt)
    if injection:
        return "injection"

    toxic, _, _ = detect_ai_toxicity(prompt)
    if toxic:
        return "toxicity"

    pii, _ = detect_pii(prompt)
    if pii:
        return "pii"

    return "safe"