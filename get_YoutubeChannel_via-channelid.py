import json
from apiclient.discovery import build

def load_config():
    config = None
    with open('.secret/config.json') as f:
        config = json.load(f)
    return config

config = load_config()

# Youtube APIトークン
YOUTUBE_API_KEY = config['external']['youtube']['api_key']
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
CHANNEL_ID = config['external']['youtube']['channel_id']

youtube = build(
    YOUTUBE_API_SERVICE_NAME,
    YOUTUBE_API_VERSION,
    developerKey=YOUTUBE_API_KEY
)

response = youtube.channels().list(
    part='snippet,statistics',
    id=CHANNEL_ID
).execute()

for item in response.get("items", []):
    if item["kind"] != "youtube#channel":
        continue
    print('*' * 10)
    print(json.dumps(item, indent=2, ensure_ascii=False))
    print('*' * 10)
