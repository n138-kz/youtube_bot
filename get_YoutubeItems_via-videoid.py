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

json_file=open('test.json', 'w')
json.dump(snippetInfo,json_file)
