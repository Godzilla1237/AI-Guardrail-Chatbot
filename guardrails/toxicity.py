def detect_toxicity(text):
    toxic_words = [
        "hate",
        "kill",
        "stupid",
        "idiot",
        "dumb",
        "hurt",
        "attack",
        "abuse"
    ]

    text = text.lower()

    for word in toxic_words:
        if word in text:
            return True, word

    return False, "None"