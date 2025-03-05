import json
import os
import sys
import math
import discord
import urllib.parse
import datetime
import time
import pytz
import logging
from apiclient.discovery import build
from discord.ext import commands, tasks

# ファイルパス
GLOBAL_FILE = {
    'config': '.secret/config.json', # 設定
    'notice_log': 'notice.json' # 通知状態管理ファイル
}

# メッセージ定義
GLOBAL_TEXT = {
    'err': {
        'en':{
            'incomplete_command': '% Incomplete command.',
        },
        'ja':{
            'incomplete_command': 'コマンドが不完全です。',
        }
    },
    'msg': {
        'en':{
        },
        'ja':{
        }
    },
}

LOCALE = 'en'

def default_config():
    config = {}
    config['internal'] = {} # require
    config['internal']['youtube'] = {} # require
    config['internal']['youtube']['notice_limit'] = 3600 # require
    config['internal']['youtube']['cycle_interval'] = 300 # require
    config['internal']['youtube']['channel_id'] = '' # require
    config['internal']['discord'] = {} # require
    config['internal']['discord']['send_message_channel'] = {} # require
    config['internal']['discord']['send_message_channel']['on_ready'] = [] # require
    config['internal']['discord']['send_message_channel']['notice'] = [] # require
    config['external'] = {} # require
    config['external']['youtube'] = {} # require
    config['external']['youtube']['api_key'] = '' # require
    config['external']['discord'] = {} # require
    config['external']['discord']['bot_token'] = '' # require
    return config

def commit_config(config=default_config(),file=GLOBAL_FILE['config']):
    config['internal']['meta'] = {}
    config['internal']['meta']['written_at'] = math.trunc(time.time())
    with open(file, mode='w') as f:
        json.dump(config, f)

def load_config(config_file=GLOBAL_FILE['config']):
    config = default_config()
    if not(os.path.isfile(config_file)):
        commit_config(config=config,file=config_file)

    with open(config_file) as f:
        config = config | json.load(f)
        commit_config(config=config,file=config_file)
    return config

def get_version(returnable=True):
    text = ''
    text += '\n'
    text += 'python\n```\n'+sys.version+'```\n'
    text += 'discordpy\n```\n'+discord.__version__+' ('+str(discord.version_info)+')'+'```\n'
    if returnable:
        return text
    else:
        print(text)

get_version(returnable=False)
config = load_config(config_file=GLOBAL_FILE['config'])

# Discord APIトークン
DISCORD_API_TOKEN = config['external']['discord']['bot_token']

# botが起動したときに送信するチャンネル一覧 type=dict
DISCORD_SEND_MESSAGE=config['internal']['discord']['send_message_channel']

# Youtube APIトークン
YOUTUBE_API_KEY = config['external']['youtube']['api_key']

# 新着動画を監視するチャンネルID
YOUTUBE_CHANNEL_ID = config['internal']['youtube']['channel_id']

# 動画投稿監視間隔 default=300s(5min)
YOUTUBE_CYCLE_INTERVAL = config['internal']['youtube']['cycle_interval']

# 通知送信タイムリミット default=3600s(a-hour)
YOUTUBE_NOTICE_LIMIT = config['internal']['youtube']['notice_limit']

# 言語
LOCALE = 'ja'

def getYoutubeItems():
    """
    * @return :Dictionary
    """
    YOUTUBE_API_SERVICE_NAME = 'youtube'
    YOUTUBE_API_VERSION = 'v3'

    youtube = build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        developerKey=YOUTUBE_API_KEY
    )

    response = youtube.search().list(
        part = "snippet",
        channelId = YOUTUBE_CHANNEL_ID,
        maxResults = 3,
        order = "date" #日付順にソート
    ).execute()

    return response

def ytb_getHelp():
    text = ''
    text += '\n'
    text += '`!ytb help`\n'
    text += 'コマンドマニュアルを表示します。\n'
    text += '`!ytb ping`\n'
    text += 'Botのレイテンシを測定します。\n'
    text += '`!ytb version`\n'
    text += 'Botのバージョンを表示します。\n'
    text += '`!ytb youtube rawitems`\n'
    text += 'Youtubeから最新の動画一覧を取得します。\n'
    text += text.replace('!ytb ','/')
    return text

def ytb_getChannelId(type='youtube'):
    if type==False:
        pass
    elif type=='youtube':
        return YOUTUBE_CHANNEL_ID
    elif type=='discord':
        return json.dumps(DISCORD_SEND_MESSAGE)

intents=discord.Intents.default()
intents.message_content = True
intents.reactions = True
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

@client.event
async def on_error(event):
    text = ''
    text += '\n'
    text += 'Called On_Error\n'

@client.event
async def on_message(message):
    try:
        # 送信者がbotである場合は弾く
        if message.author.bot:
            return
        
        # テキストチャンネルのみ処理
        if message.channel.type != discord.ChannelType.text:
            return
        
        if message.content.startswith('!ytb'):
            print(f'on_message: {message.content}')

            if message.content == "!ytb help":
                print(f'do_action: {message.content}')

                await message.reply(ytb_getHelp())
            elif message.content == "!ytb ping":
                # Ping値を測定 [Ping値を測定](https://discordbot.jp/blog/16/)
                print(f'do_action: {message.content}')

                # Ping値を秒単位で取得
                raw_ping = client.latency

                # ミリ秒に変換して丸める
                ping = round(raw_ping * 1000)

                text = f'Pong!\nBotのPing値は{ping}msです。'

                # 送信する
                print(text)
                await message.reply(text)
            elif message.content == "!ytb version":
                print(f'do_action: {message.content}')
                text = ''
                text += 'Current version is below.\n{}'.format(get_version())
                
                await message.reply(text)
            elif message.content == "!ytb youtube rawitems":
                print(f'do_action: {message.content}')
                data1=getYoutubeItems()
                data2=[]
                data3=''
                for item in data1['items']:
                    data2.append({
                        'publishedAt': item['snippet']['publishedAt'],
                        'channelId': item['snippet']['channelId'],
                        'title': urllib.parse.unquote(item['snippet']['title']).replace('&quot;', '"'),
                        'description': item['snippet']['description'],
                        'id': item['id']['videoId'],
                        'thumbnails': item['snippet']['thumbnails']['high'],
                    })
                    data3+='- {2}\n[{0}]({1})\n'.format(
                        data2[len(data2)-1]['title'],
                        'https://www.youtube.com/watch?v='+data2[len(data2)-1]['id'],
                        data2[len(data2)-1]['publishedAt'],
                    )
                with open('detail.json','w', encoding="utf-8") as f:
                    json.dump(data1, f, ensure_ascii=False, indent=4)
                with open('result.json','w', encoding="utf-8") as f:
                    json.dump(data2, f, ensure_ascii=False, indent=4)
                text = ''
                text += '\n'
                text += data3+'\n'

                await message.reply(text, files=[discord.File('result.json'),discord.File('detail.json')])
            else:
                print(f'do_action: not recognised commands')

                text = 'Not recognised commands.\n'
                text += 'Hint: Run `!ytb help`\n'

                await message.reply(text)
    except:
        pass

@tasks.loop(seconds=YOUTUBE_CYCLE_INTERVAL)
async def loops():
    logging.basicConfig(level=logging.ERROR)
    try:
        YOUTUBE_CONTENTS=getYoutubeItems()
        data=[]
        console=''
        for item in YOUTUBE_CONTENTS['items']:
            file=GLOBAL_FILE['notice_log']
            notice=[]
            if not(os.path.exists(file)):
                with open(file,mode='w',encoding='UTF-8') as f:
                    json.dump([],f)
            if os.path.isfile(file):
                with open(file,encoding='UTF-8') as f:
                    notice=json.load(f)
            else:
                print(f'Unable access to "{file}"')
                sys.exit(1)           

            data.append({
                'publishedAt': math.trunc(datetime.datetime.fromisoformat(item['snippet']['publishedAt'].replace('Z', '+00:00')).astimezone(pytz.utc).timestamp()),
                'channel_id': item['snippet']['channelId'],
                'title': urllib.parse.unquote(item['snippet']['title']).replace('&quot;', '"'),
                'video_id': item['id']['videoId'],
                'flag': 0,
            })
            if abs(math.trunc(time.time())-data[len(data)-1]['publishedAt'])>YOUTUBE_NOTICE_LIMIT:
                data[len(data)-1]['flag']=data[len(data)-1]['flag']|1
            for l in notice:
                if l['video_id'] == data[len(data)-1]['video_id']:
                    data[len(data)-1]['flag']=data[len(data)-1]['flag']|2
            
            if data[len(data)-1]['flag']==0:
                for channel_id in DISCORD_SEND_MESSAGE['notice']:
                    channel = client.get_channel(channel_id)
                    await channel.send('動画がアップロードされました。\n[{0}]({1})\n{1}'.format(
                        data[len(data)-1]['title'],
                        'https://www.youtube.com/watch?v='+data[len(data)-1]['video_id'],
                    ))
                    data[len(data)-1]['flag']=data[len(data)-1]['flag']|2

            with open(file,mode='w',encoding='UTF-8') as f:
                json.dump(data,f,ensure_ascii=False,indent=4)

            console+='[{3}] {2} [{0}] {1}\n'.format(
                data[len(data)-1]['video_id'],
                data[len(data)-1]['title'],
                data[len(data)-1]['publishedAt'],
                '{}'.format(data[len(data)-1]['flag']),
            )
        print(f'{console}')
    except Exception as e:
        logging.error(f'Error has occured: {e}')
        print(f'Error has occured: \n{e}')
        for channel_id in DISCORD_SEND_MESSAGE['on_ready']:
            channel = client.get_channel(channel_id)
            await channel.send(f'Error has occured: \n```\n{e}\n```\n')

@tree.command(name="help",description="コマンドヘルプを表示します。")
async def help(interaction: discord.Interaction):
    await interaction.response.send_message(ytb_getHelp(),ephemeral=True)#ephemeral=True→「これらはあなただけに表示されています」

@tree.command(name="ping",description="Botのレイテンシを測定します。")
async def ping(interaction: discord.Interaction):
    # Ping値を秒単位で取得
    raw_ping = client.latency

    # ミリ秒に変換して丸める
    ping = round(raw_ping * 1000)

    # 送信する
    await interaction.response.send_message(f"Pong!\nBotのPing値は{ping}msです。",ephemeral=True)#ephemeral=True→「これらはあなただけに表示されています」

@tree.command(name="version",description="Botのバージョンを表示します。")
async def version(interaction: discord.Interaction):
    # 送信する
    await interaction.response.send_message("Current version is below.\n{}".format(get_version()),ephemeral=True)#ephemeral=True→「これらはあなただけに表示されています」

    # 送信する
    await interaction.response.send_message("Current version is below.\n{}".format(get_version()),ephemeral=True)#ephemeral=True→「これらはあなただけに表示されています」

# botが起動したときの処理 [discord.pyを使用したdiscord botの作り方](https://qiita.com/TakeMimi/items/1e2d76eecc25e92c93ef#210-ver)
@client.event
async def on_ready():
    print(client.user.name.capitalize()+"が起動しました")

    print('--設定情報--')
    print('[Discord]')
    print('起動メッセージ送信先: ',end='')
    for s in DISCORD_SEND_MESSAGE['on_ready']:
        print('{},'.format(s),end='')
    print('')
    print('通知メッセージ送信先: ',end='')
    for s in DISCORD_SEND_MESSAGE['notice']:
        print('{},'.format(s),end='')
    print('\n')
    print('[Youtube]')
    print('動画投稿監視チャンネル: {}'.format(YOUTUBE_CHANNEL_ID))
    print('動画投稿監視間隔: {}'.format(YOUTUBE_CYCLE_INTERVAL))
    print('通知送信タイムリミット: {}'.format(YOUTUBE_NOTICE_LIMIT))
    print('--設定情報--\n')

    #スラッシュコマンドを同期
    await tree.sync()

    # アクティビティステータスを設定
    # https://qiita.com/ryo_001339/items/d20777035c0f67911454
    await client.change_presence(status=discord.Status.online, activity=discord.CustomActivity(name='`!ytb help`'))

    # 起動メッセージ送信
    for channel_id in DISCORD_SEND_MESSAGE['on_ready']:
        print('Discord channel({0})に起動メッセージ送信中'.format(
            channel_id
        ))
        channel = client.get_channel(channel_id)
        await channel.send('{0}'.format(
            client.user.name.capitalize()+"が起動しました",
        ))
        print('Discord channel({0})に起動メッセージ送信完了'.format(
            channel_id
        ))

    loops.start()

# botを起動
client.run(DISCORD_API_TOKEN)
