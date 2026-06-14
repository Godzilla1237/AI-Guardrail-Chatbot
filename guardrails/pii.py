import re
from presidio_analyzer import AnalyzerEngine

_analyzer = None


def load_pii_analyzer():
    global _analyzer

    if _analyzer is None:
        _analyzer = AnalyzerEngine()

    return _analyzer


def detect_pii(text):
    analyzer = load_pii_analyzer()

    results = analyzer.analyze(
        text=text,
        language="en"
    )

    if results:
        entity = results[0].entity_type
        score = round(results[0].score, 2)
        return True, f"{entity} score={score}"

    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    phone_pattern = r"\b[6-9]\d{9}\b"
    aadhaar_pattern = r"\b\d{4}\s?\d{4}\s?\d{4}\b"

    if re.search(email_pattern, text):
        return True, "Email Regex"

    if re.search(phone_pattern, text):
        return True, "Phone Number Regex"

    if re.search(aadhaar_pattern, text):
        return True, "Aadhaar-like Number Regex"

    return False, "None"