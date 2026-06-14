from detoxify import Detoxify

result = Detoxify('original').predict(
    "I hate everyone"
)

print(result)