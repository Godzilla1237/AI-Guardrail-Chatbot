from detoxify import Detoxify

_model = None


def load_toxicity_model():
    global _model

    if _model is None:
        _model = Detoxify("original")

    return _model


def detect_ai_toxicity(text, threshold=0.70):
    model = load_toxicity_model()

    result = model.predict(text)

    toxicity_score = float(result["toxicity"])
    severe_toxicity_score = float(result["severe_toxicity"])
    insult_score = float(result["insult"])
    threat_score = float(result["threat"])
    obscene_score = float(result["obscene"])
    identity_attack_score = float(result["identity_attack"])

    scores = {
        "toxicity": toxicity_score,
        "severe_toxicity": severe_toxicity_score,
        "insult": insult_score,
        "threat": threat_score,
        "obscene": obscene_score,
        "identity_attack": identity_attack_score
    }

    highest_category = max(scores, key=scores.get)
    highest_score = scores[highest_category]

    if highest_score >= threshold:
        return True, highest_category, highest_score

    return False, highest_category, highest_score