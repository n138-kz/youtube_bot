import json
import sys
import discord
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

intents=discord.Intents.default()
intents.message_content = True
intents.reactions = True
client = discord.Client(intents=intents)
#client = discord.Client(intents=discord.Intents.all())

# botが起動したときの処理 [discord.pyを使用したdiscord botの作り方](https://qiita.com/TakeMimi/items/1e2d76eecc25e92c93ef#210-ver)
@client.event
async def on_ready():
    print("Botが立ち上がったよ！")

@client.event
async def on_message(message):
    # Ping値を測定 [Ping値を測定](https://discordbot.jp/blog/16/)
    if message.content == "/ping":
        # Ping値を秒単位で取得
        raw_ping = client.latency

        # ミリ秒に変換して丸める
        ping = round(raw_ping * 1000)

        # 送信する
        await message.reply(f"Pong!\nBotのPing値は{ping}msです。")
    if message.content == "/version":
        await message.reply(print_version())
        

# botを起動
client.run(DISCORD_API_TOKEN)
