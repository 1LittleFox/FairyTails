import json

with open("/tts-credentials.json", 'r') as f:
    data = json.load(f)

# Получите строку для .env
credentials_string = json.dumps(data, separators=(',', ':'))
print(credentials_string)
