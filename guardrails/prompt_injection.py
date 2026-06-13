def detect_prompt_injection(text):
    
    phrases = [
        "ignore previous instructions",
        "forget your instructions",
        "act as",
        "jailbreak",
        "developer mode",
        "dan mode"
    ]

    text = text.lower()

    for phrase in phrases:
        if phrase in text:
            return True, phrase

    return False, "None"