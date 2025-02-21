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

def load_config():
    config = None
    with open('.secret/config.json') as f:
        config = json.load(f)
    return config

def print_version():
    print("python: "+sys.version)
    print("discordpy: "+discord.__version__+' ('+str(discord.version_info)+')')

print_version()
config = load_config()

# Discord APIトークン
DISCORD_API_TOKEN = config['external']['discord']['bot_token']

# botが起動したときに送信するチャンネル一覧
DISCORD_SEND_MESSAGE=config['internal']['discord']['send_message_channel']

# Youtube APIトークン
YOUTUBE_API_KEY = config['external']['youtube']['api_key']

# 新着動画を監視するチャンネルID
YOUTUBE_CHANNEL_ID = config['internal']['youtube']['channel_id']

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
        
        if message.content.startswith('!ytb'):
            print(f'on_message: {message.content}')

            if message.content == "!ytb help":
                print(f'do_action: {message.content}')
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
                print(text)
                await message.reply(text)
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
                text += 'Current version is below.\n'
                text += 'python\n```\n'+sys.version+'```\n'
                text += 'discordpy\n```\n'+discord.__version__+' ('+str(discord.version_info)+')'+'```\n'
                print(text)
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
                print(text)
                await message.reply(text, files=[discord.File('result.json'),discord.File('detail.json')])
            else:
                print(f'do_action: not recognised commands')

                text = 'Not recognised commands.\n'
                text += 'Hint: Run `!ytb help`\n'
                print(text)
                await message.reply(text)
    except:
        sys.exit()

@tasks.loop(seconds=config['internal']['youtube']['cycle_interval'])
async def loops():
    logging.basicConfig(level=logging.ERROR)
    try:
        YOUTUBE_CONTENTS=getYoutubeItems()
        data=[]
        console=''
        for item in YOUTUBE_CONTENTS['items']:
            file='notice.json'
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
            if abs(math.trunc(time.time())-data[len(data)-1]['publishedAt'])>config['internal']['youtube']['notice_limit']:
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
    text = ''
    text += '\n'
    text += 'python\n```\n'+sys.version+'```\n'
    text += 'discordpy\n```\n'+discord.__version__+' ('+str(discord.version_info)+')'+'```\n'

    # 送信する
    await interaction.response.send_message(f"Current version is below.\n{text}",ephemeral=True)#ephemeral=True→「これらはあなただけに表示されています」

# botが起動したときの処理 [discord.pyを使用したdiscord botの作り方](https://qiita.com/TakeMimi/items/1e2d76eecc25e92c93ef#210-ver)
@client.event
async def on_ready():
    print(client.user.name.capitalize()+"が起動しました")

    print('--設定情報--')
    print('[Discord]')
    print('起動メッセージ送信先: ',end='')
    for s in config['internal']['discord']['send_message_channel']['on_ready']:
        print('{},'.format(s),end='')
    print('')
    print('通知メッセージ送信先: ',end='')
    for s in config['internal']['discord']['send_message_channel']['notice']:
        print('{},'.format(s),end='')
    print('')
    print('[Youtube]')
    print('動画投稿監視チャンネル: {}'.format(YOUTUBE_CHANNEL_ID))
    print('動画投稿監視間隔: {}'.format(config['internal']['youtube']['cycle_interval']))
    print('通知送信タイムリミット: {}'.format(config['internal']['youtube']['notice_limit']))
    print('--設定情報--\n')

    #スラッシュコマンドを同期
    await tree.sync()

    for channel_id in DISCORD_SEND_MESSAGE['on_ready']:
        print('Discord channel({0})に起動メッセージ送信中'.format(
            channel_id
        ))
        channel = client.get_channel(channel_id)
        await channel.send('{0}\n{1}'.format(
            client.user.name.capitalize()+"が起動しました",
            '[Discord Developers Console](https://discord.com/developers/applications/1342289249365659778)',
        ))
        print('Discord channel({0})に起動メッセージ送信完了'.format(
            channel_id
        ))

    loops.start()

# botを起動
client.run(DISCORD_API_TOKEN)
