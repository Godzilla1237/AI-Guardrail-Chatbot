import re

def detect_pii(text):

    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    phone_pattern = r"\b[6-9]\d{9}\b"

    if re.search(email_pattern, text):
        return True, "Email"

    if re.search(phone_pattern, text):
        return True, "Phone Number"

    return False, "None"