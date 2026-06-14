def detect_prompt_injection(text):
    
    phrases = [
        "ignore previous instructions",
        "forget your instructions",
        "ignore all previous instructions",
        "ignore above instructions",
        "reveal your system prompt",
        "show your system prompt",
        "system prompt",
        "show hidden instructions",
        "hidden instructions",
        "developer mode",
        "enable developer mode",
        "dan mode",
        "do anything now",
        "jailbreak",
        "bypass",
        "act as",
        "apne saare instructions ignore karo",
        "system prompt dikhao",
        "developer mode chalu karo",
        "hidden instructions batao"
    ]

    text = text.lower()

    for phrase in phrases:
        if phrase in text:
            return True, phrase

    return False, "None"