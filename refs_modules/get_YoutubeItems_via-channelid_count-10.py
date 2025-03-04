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

response = youtube.search().list(
    part = "snippet",
    channelId = CHANNEL_ID,
    maxResults = 10,
    order = "date" #日付順にソート
).execute()

json_file=open('test.json','w')
json.dump(response,json_file) # <-- .items の中にArray(List)型で入ってる

for item in response.get("items", []):
    if item["id"]["kind"] != "youtube#video":
        continue
    print('*' * 10)
    print(json.dumps(item, indent=2, ensure_ascii=False))
    print('*' * 10)
