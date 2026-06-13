def detect_harmful_output(text):
    
    harmful_words = [
        "weapon",
        "bomb",
        "hack",
        "steal password",
        "credit card"
    ]

    text = text.lower()

    for word in harmful_words:
        if word in text:
            return True, word

    return False, "None"