import json
import sys
import discord

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

