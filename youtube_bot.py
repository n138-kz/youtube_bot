import json
import os
import sys
import discord
import http.client
from urllib.parse import urlencode
from datetime import datetime
from googleapiclient.discovery import build

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
    service = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    request = service.channels().list(
        part = 'statistics',
        # forUsername = '',
        id = YOUTUBE_CHANNEL_ID
    )
    return request.execute()

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
        if message.content == "!help":
            text = ''
            text += '\n'
            text += '`!help`\n'
            text += 'コマンドマニュアルを表示します。\n'
            text += '`!ping`\n'
            text += 'Botのレイテンシを測定します。\n'
            text += '`!version`\n'
            text += 'Botのバージョンを表示します。\n'
            text += '`!youtuberawitems`\n'
            text += 'Youtubeから動画一覧を取得します。\n'
            await message.reply(f"{text}")
        # Ping値を測定 [Ping値を測定](https://discordbot.jp/blog/16/)
        if message.content == "!ping":
            # Ping値を秒単位で取得
            raw_ping = client.latency

            # ミリ秒に変換して丸める
            ping = round(raw_ping * 1000)

            # 送信する
            await message.reply(f"Pong!\nBotのPing値は{ping}msです。")
        if message.content == "!version":
            text = ''
            text += '\n'
            text += 'python\n```\n'+sys.version+'```\n'
            text += 'discordpy\n```\n'+discord.__version__+' ('+str(discord.version_info)+')'+'```\n'
            await message.reply(f"Current version is below.\n{text}")
        if message.content == "!youtuberawitems":
            text = ''
            text += '\n'
            text += getYoutubeItems()
            await message.reply(f"{text}")
    except:
        sys.exit()

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
    print(client.user.name+"が起動しました")

    #スラッシュコマンドを同期
    await tree.sync()

    for channel_id in DISCORD_SEND_MESSAGE['on_ready']:
        channel = client.get_channel(channel_id)
        await channel.send(client.user.name+"が起動しました")
        await channel.send('[Discord Developers Console](https://discord.com/developers/applications/1342289249365659778)')

# botを起動
client.run(DISCORD_API_TOKEN)
