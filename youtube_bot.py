import json

def load_config():
    config = None
    with open('.secret/config.json') as f:
        config = json.load(f)
    return config

config = load_config()

