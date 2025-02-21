import json
import os
import sys
import discord
import http.client
import urllib.parse
from datetime import datetime
from apiclient.discovery import build
from discord.ext import commands, tasks

def load_config():
    config = None
    with open('.secret/config.json') as f:
        config = json.load(f)
    return config

def print_version():
    print("version")
    print("python: "+sys.version)
    print("discordpy: "+discord.__version__+' ('+str(discord.version_info)+')')

print_version()
config = load_config()

# Discord APIトークン
DISCORD_API_TOKEN = config['external']['discord']['bot_token']

# botが起動したときに送信するチャンネル一覧
DISCORD_SEND_MESSAGE=config['external']['discord']['send_message_channel']

# Youtube APIトークン
YOUTUBE_API_KEY = config['external']['youtube']['api_key']

# 新着動画を監視するチャンネルID
YOUTUBE_CHANNEL_ID = config['external']['youtube']['channel_id']

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
        
        print(f'on_message: {message.content}')

        if message.content == "!help":
            print(f'do_action: {message.content}')
            text = ''
            text += '\n'
            text += '`!help`\n'
            text += 'コマンドマニュアルを表示します。\n'
            text += '`!ping`\n'
            text += 'Botのレイテンシを測定します。\n'
            text += '`!version`\n'
            text += 'Botのバージョンを表示します。\n'
            text += '`!youtube rawitems`\n'
            text += 'Youtubeから動画一覧を取得します。\n'
            print(text)
            await message.reply(text)
        # Ping値を測定 [Ping値を測定](https://discordbot.jp/blog/16/)
        if message.content == "!ping":
            print(f'do_action: {message.content}')
            # Ping値を秒単位で取得
            raw_ping = client.latency

            # ミリ秒に変換して丸める
            ping = round(raw_ping * 1000)

            text = f'Pong!\nBotのPing値は{ping}msです。'

            # 送信する
            print(text)
            await message.reply(text)
        if message.content == "!version":
            print(f'do_action: {message.content}')
            text = ''
            text += 'Current version is below.\n'
            text += 'python\n```\n'+sys.version+'```\n'
            text += 'discordpy\n```\n'+discord.__version__+' ('+str(discord.version_info)+')'+'```\n'
            print(text)
            await message.reply(text)
        if message.content == "!youtube rawitems":
            print(f'do_action: {message.content}')
            data1=getYoutubeItems()
            data2=[]
            data3=''
            for item in data1['items']:
                data2.append({
                    'publishedAt': item['snippet']['publishedAt'],
                    'channelId': item['snippet']['channelId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'id': item['id']['videoId'],
                    'thumbnails': item['snippet']['thumbnails']['high'],
                })
                data3+='- {2}\n[{0}]({1})\n'.format(urllib.parse.unquote(item['snippet']['title']).replace('&quot;', '"'),'https://www.youtube.com/watch?v='+item['id']['videoId'],item['snippet']['publishedAt'])
            with open('detail.json','w', encoding="utf-8") as f:
                json.dump(data1, f, ensure_ascii=False, indent=4)
            with open('result.json','w', encoding="utf-8") as f:
                json.dump(data2, f, ensure_ascii=False, indent=4)
            text = ''
            text += '\n'
            text += data3+'\n'
            print(text)
            await message.reply(text, file=discord.File('result.json'))
    except:
        sys.exit()

@tasks.loop(seconds=30)
async def loops():
    print('',end='')

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

    #スラッシュコマンドを同期
    await tree.sync()

    for channel_id in DISCORD_SEND_MESSAGE['on_ready']:
        channel = client.get_channel(channel_id)
        await channel.send(client.user.name.capitalize()+"が起動しました")
        await channel.send('[Discord Developers Console](https://discord.com/developers/applications/1342289249365659778)')

# botを起動
client.run(DISCORD_API_TOKEN)
