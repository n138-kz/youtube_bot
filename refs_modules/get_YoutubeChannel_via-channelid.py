import os
import json
from apiclient.discovery import build

def load_config():
    config = None
    # 現在のスクリプトファイルのディレクトリを取得
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 1つ上の階層のディレクトリパスを取得
    parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))

    # 1つ上の階層にあるファイルのパスを作成
    file_path = os.path.join(parent_dir, '.secret/config.json')

    with open(file_path) as f:
        config = json.load(f)
    return config

config = load_config()

# Youtube APIトークン
YOUTUBE_API_KEY = config['external']['youtube']['api_key']
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
CHANNEL_ID = config['internal']['youtube']['channel_id']

youtube = build(
    YOUTUBE_API_SERVICE_NAME,
    YOUTUBE_API_VERSION,
    developerKey=YOUTUBE_API_KEY
)

response = youtube.channels().list(
    part='snippet,statistics',
    id=CHANNEL_ID
).execute()

with open(os.path.splitext(os.path.basename(__file__))[0]+'.json',mode='w',encoding='UTF-8') as f:
    json.dump(obj=response,fp=f, indent=2, ensure_ascii=False)

for item in response.get("items", []):
    if item["kind"] != "youtube#channel":
        continue
    print('*' * 10)
    print(json.dumps(item, indent=2, ensure_ascii=False))
    print('*' * 10)
