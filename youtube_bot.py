import json
import discord

def load_config():
    config = None
    with open('.secret/config.json') as f:
        config = json.load(f)
    return config

config = load_config()

# Discord APIトークン
DISCORD_API_TOKEN = config['external']['discord']['bot_token']

print(discord.version_info)
