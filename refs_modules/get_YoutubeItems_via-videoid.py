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

# Youtube動画ID
videoId = 'OgYWssWn7uQ'

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
videos_response = youtube.videos().list(
    part='snippet,statistics',
    id='{},'.format(videoId)
).execute()
# snippet
snippetInfo = videos_response["items"][0]["snippet"]
# 動画タイトル
title = snippetInfo['title']
# チャンネル名
channeltitle = snippetInfo['channelTitle']
print(channeltitle)
print(title)
print(f'https://www.youtube.com/watch?v={videoId}')

with open(os.path.splitext(os.path.basename(__file__))[0]+'.json',mode='w',encoding='UTF-8') as f:
    json.dump(obj=snippetInfo,fp=f, indent=2, ensure_ascii=False)
