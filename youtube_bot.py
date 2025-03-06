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
import traceback
from apiclient.discovery import build
from discord.ext import commands, tasks

# ファイルパス
GLOBAL_FILE = {
    'config': '.secret/config.json', # 設定
    'notice_log': 'notice.json', # 通知状態管理ファイル
    'except_log': 'except.log',
    'async_log': 'log/async_%time.log',
}

# メッセージ定義
GLOBAL_TEXT = {
    'err': {
        'en':{
            'incomplete_command': '% Incomplete command.',
            'your_not_admin': 'Your NOT Administrators.',
        },
        'ja':{
            'incomplete_command': 'コマンドが不完全です。',
            'your_not_admin': 'あなたは管理者ロールが付与されていません。',
        }
    },
    'msg': {
        'en':{
        },
        'ja':{
        }
    },
    'url': {
        'github': {
            'repository': 'https://github.com/n138-kz/youtube_bot',
        }
    }
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
    with open(file, mode='w',encoding='UTF-8') as f:
        json.dump(config, f, indent=4)

def load_config(config_file=GLOBAL_FILE['config']):
    config = default_config()
    if not(os.path.isfile(config_file)):
        commit_config(config=config,file=config_file)

    with open(config_file,encoding='UTF-8') as f:
        config = config | json.load(f)
        commit_config(config=config,file=config_file)
    return config

def get_version(returnable=True,markdown=False):
    text = ''
    text += '\n'
    if markdown:
        text += 'python\n```\n'+sys.version+'```\n'
    else:
        text += 'python: '+sys.version+'\n'
    if markdown:
        text += 'discordpy\n```\n'+discord.__version__+' ('+str(discord.version_info)+')'+'```\n'
    else:
        text += 'discordpy: '+discord.__version__+' ('+str(discord.version_info)+')'+'\n'
    if returnable:
        return text
    else:
        print(text.replace('`',''))

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

# Youtube API Access path
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

# 言語
LOCALE = 'ja'

def getYoutubeItems():
    """
    * @return :Dictionary
    """
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

def getYoutubeChannels(channel_id=YOUTUBE_CHANNEL_ID):
    """
    * @return :Dictionary
    """
    youtube = build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        developerKey=YOUTUBE_API_KEY
    )

    response = youtube.channels().list(
        part='snippet,statistics',
        id=channel_id
    ).execute()

    for item in response.get("items", []):
        if item["kind"] != "youtube#channel":
            continue
        return item

def getHumanableTime(second=0,mode='arr',format='%H:%m:%S'):
    """
    @args
    second: int; i<=0
    mode: str; i=["arr", 'str']
    format: str; i='%H:%m:%S'
    """
    time=[0,0,second]
    while second>=60:
        if False:
            pass
        elif second>=3600:
            time[0]+=1
            second-=3600
        elif second>=60:
            time[1]+=1
            second-=60
    time[2]=second

    if mode=='arr':
        return time
    elif mode=='str':
        text=format
        text=text.replace('%H', str(time[0]).zfill(2))
        text=text.replace('%m', str(time[1]).zfill(2))
        text=text.replace('%S', str(time[2]).zfill(2))
        return text

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
    text += '`!ytb upload notice.json`\n'
    text += '(管理者コマンド)\n'
    text += '通知状態管理ファイルをアップロードします。\n'
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
            global YOUTUBE_CHANNEL_ID

            if False:
                pass
            elif message.content.startswith('!ytb help'):
                print(f'do_action: {message.content}')
                print(f'do_author: {message.author.name}')

                await message.reply(ytb_getHelp())
            elif message.content.startswith('!ytb ping'):
                # Ping値を測定 [Ping値を測定](https://discordbot.jp/blog/16/)
                print(f'do_action: {message.content}')
                print(f'do_author: {message.author.name}')

                # Ping値を秒単位で取得
                raw_ping = client.latency

                # ミリ秒に変換して丸める
                ping = round(raw_ping * 1000)

                text = f'Pong!\nBotのPing値は{ping}msです。'

                # 送信する
                print(text)
                await message.reply(text)
            elif message.content.startswith('!ytb version'):
                print(f'do_action: {message.content}')
                print(f'do_author: {message.author.name}')
                text = ''
                text += 'Current version is below.\n{}'.format(get_version())
                
                await message.reply(text)
            elif message.content.startswith('!ytb upload notice.json'):
                print(f'do_action: {message.content}')
                print(f'do_author: {message.author.name}')
                # 管理者コマンド
                if message.author.guild_permissions.administrator:
                    file=GLOBAL_FILE['notice_log']
                    if not(os.path.exists(file)):
                        with open(file,mode='w',encoding='UTF-8') as f:
                            json.dump([],f)
                        embed = discord.Embed(title=file,color=0x00ff00)
                    await message.reply(embed=embed,files=[discord.File(file)])
                else:
                    embed = discord.Embed(title='Error',description=GLOBAL_TEXT['err'][LOCALE]['your_not_admin'],color=0xff0000)
                    await message.reply(embed=embed)
            elif message.content.startswith('!ytb youtube set channel'):
                print(f'do_action: {message.content}')
                print(f'do_author: {message.author.name}')
                # 管理者コマンド
                if message.author.guild_permissions.administrator:
                    id_old=ytb_getChannelId(type='youtube')
                    id_new=message.content.replace('!ytb youtube set channel','').strip()

                    text=''
                    text+=''
                    text+='Command: `{0}`\nYoutube channel-id has changed.'.format(
                        message.content,
                    )

                    channel_info_old=getYoutubeChannels(channel_id=id_old)
                    channel_info_new=getYoutubeChannels(channel_id=id_new)

                    embed = discord.Embed(title='Commit',description=text,color=0x00ff00)
                    embed.add_field(
                        name='Before: '+id_old,
                        value='ID: [{0}](https://www.youtube.com/channel/{0})\nName: [{1}](https://www.youtube.com/channel/{0})\n[thumbnails]({2})\nView:{3}\nSubscriber:{4}\nVideo:{5}'.format(
                            id_old,
                            channel_info_old['snippet']['title'],
                            channel_info_old['snippet']['thumbnails']['default']['url'],
                            channel_info_old['statistics']['viewCount'],
                            channel_info_old['statistics']['subscriberCount'],
                            channel_info_old['statistics']['videoCount'],
                        ),
                        inline=False
                    )
                    embed.add_field(
                        name='After: '+id_new,
                        value='ID: [{0}](https://www.youtube.com/channel/{0})\nName: [{1}](https://www.youtube.com/channel/{0})\n[thumbnails]({2})\nView:{3}\nSubscriber:{4}\nVideo:{5}'.format(
                            id_new,
                            channel_info_new['snippet']['title'],
                            channel_info_new['snippet']['thumbnails']['default']['url'],
                            channel_info_new['statistics']['viewCount'],
                            channel_info_new['statistics']['subscriberCount'],
                            channel_info_new['statistics']['videoCount'],
                        ),
                        inline=False
                    )
                    embed.set_thumbnail(url=channel_info_new['snippet']['thumbnails']['default']['url'])

                    YOUTUBE_CHANNEL_ID = config['internal']['youtube']['channel_id']
                    config['internal']['youtube']['channel_id'] = id_new
                    commit_config(config)

                    print(await message.reply(embed=embed))
                else:
                    embed = discord.Embed(title='Error',description=GLOBAL_TEXT['err'][LOCALE]['your_not_admin'],color=0xff0000)
                    print(await message.reply(embed=embed))
            elif message.content.startswith('!ytb youtube rawitems'):
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
    except Exception as e:
        print('Exception:')
        traceback.print_exc()

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
        logging.error('Error has occured: {}'.format(e.reason))
        print('Error has occured: {}'.format(e.reason))
        for channel_id in DISCORD_SEND_MESSAGE['on_ready']:
            channel = client.get_channel(channel_id)
            file = GLOBAL_FILE['except_log']
            text = '{0}\n\n<Except reason>\n{1}\n\n<Except content>\n{2}\n\n<Except error_details>\n{3}\n'.format(
                e,
                e.reason,
                e.content,
                e.error_details,
            )
            with open(file,mode='w',encoding='UTF-8') as f:
                print(text,file=f)

            embed = discord.Embed(
                title='Error has occured',
                description='```\n{}\n```'.format(e.reason),
                color=0xff0000,
                url=GLOBAL_TEXT['url']['github']['repository'],
            )
            await channel.send(embed=embed)
            await channel.send(files=[discord.File(file)])

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

@tree.command(name="youtube",description="YoutubeAPIにアクセスします。")
async def youtube(interaction: discord.Interaction):
    # 送信する
    await interaction.response.send_message(GLOBAL_TEXT['err'][LOCALE]['incomplete_command'],ephemeral=True)#ephemeral=True→「これらはあなただけに表示されています」

@tree.command(name="upload",description="コマンドヘルプを参照してください。")
async def upload(interaction: discord.Interaction):
    # 送信する
    await interaction.response.send_message(GLOBAL_TEXT['err'][LOCALE]['incomplete_command'],ephemeral=True)#ephemeral=True→「これらはあなただけに表示されています」

# botが起動したときの処理 [discord.pyを使用したdiscord botの作り方](https://qiita.com/TakeMimi/items/1e2d76eecc25e92c93ef#210-ver)
@client.event
async def on_ready():
    text_print=''
    text_print+=''
    text_print+='--設定情報--\n\n'
    text_markdown=''
    text_markdown+=''

    text_print+=''
    text_markdown+=''
    text_print+='[Discord]\n'
    text_markdown+='[Discord]\n'
    text_print+='Bot name: `{0}`\n'.format(client.user.name.capitalize())
    text_markdown+='Bot name: [{0}](https://discord.com/developers/applications/{1})({1})\n'.format(client.user.name.capitalize(),client.user.id)
    text_print+='起動メッセージ送信先: '
    text_markdown+='起動メッセージ送信先:\n'
    for s in DISCORD_SEND_MESSAGE['on_ready']:
        channel = client.get_channel(s)
        guild = channel.guild
        text_print+='{0}({3}: {1}),'.format(s,channel.name,guild.id,guild.name)
        text_markdown+='- [{0}](https://discord.com/channels/{2}/{0}/)({3}: {1})\n'.format(s,channel.name,guild.id,guild.name)
    text_print+='\n'
    text_print+='通知メッセージ送信先: '
    text_markdown+='通知メッセージ送信先:\n'
    for s in DISCORD_SEND_MESSAGE['notice']:
        channel = client.get_channel(s)
        guild = channel.guild
        guild_id = guild.id
        text_print+='{0}({3}: {1}),'.format(s,channel.name,guild.id,guild.name)
        text_markdown+='- [{0}](https://discord.com/channels/{2}/{0}/)({3}: {1})\n'.format(s,channel.name,guild.id,guild.name)
    text_print+='\n'
    text_print+='\n'
    text_markdown+='\n'

    text_print+='[Youtube]\n'
    text_markdown+='[Youtube]\n'
    text_print+='動画投稿監視チャンネル: `{}`\n'.format(YOUTUBE_CHANNEL_ID)
    text_markdown+='動画投稿監視チャンネル: [{0}](https://www.youtube.com/channel/{0})\n'.format(YOUTUBE_CHANNEL_ID)
    text_print+='動画投稿監視間隔: `{0}`({1})\n'.format(YOUTUBE_CYCLE_INTERVAL,getHumanableTime(second=YOUTUBE_CYCLE_INTERVAL,mode='str'))
    text_markdown+='動画投稿監視間隔: `{0}`({1})\n'.format(YOUTUBE_CYCLE_INTERVAL,getHumanableTime(second=YOUTUBE_CYCLE_INTERVAL,mode='str'))
    text_print+='通知送信タイムリミット: `{0}`({1})\n'.format(YOUTUBE_NOTICE_LIMIT,getHumanableTime(second=YOUTUBE_NOTICE_LIMIT,mode='str'))
    text_markdown+='通知送信タイムリミット: `{0}`({1})\n'.format(YOUTUBE_NOTICE_LIMIT,getHumanableTime(second=YOUTUBE_NOTICE_LIMIT,mode='str'))
    text_print+='\n'
    text_markdown+='\n'

    print(text_print.replace('`',''))

    #スラッシュコマンドを同期
    await tree.sync()

    # アクティビティステータスを設定
    # https://qiita.com/ryo_001339/items/d20777035c0f67911454
    await client.change_presence(status=discord.Status.online, activity=discord.CustomActivity(name='!ytb help'))

    # 起動メッセージ送信
    for channel_id in DISCORD_SEND_MESSAGE['on_ready']:
        try:
            guild = channel.guild
            guild_id = guild.id

            print('Discord channel({0}/{1})に起動メッセージ送信中: '.format( guild_id,channel_id ),end='')
            channel = client.get_channel(channel_id)
            embed = discord.Embed(
                title=client.user.name.capitalize(),
                description='{0}が起動しました。'.format(client.user.name.capitalize()),
                color=0x00ff00,
                url=GLOBAL_TEXT['url']['github']['repository'],
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )
            embed.add_field(name='設定情報',value=text_markdown,inline=False)
            embed.set_thumbnail(url=client.user.avatar.url)
            response = await channel.send(embed=embed)
            file='{0}/{1}'.format(
                os.getcwd(),
                GLOBAL_FILE['async_log'].replace('%time',str(math.trunc(time.time())))
            )
            if not(os.path.isdir(os.path.dirname(file))):
                os.mkdir(os.path.dirname(file))
            with open(file,encoding='UTF-8',mode='w') as f:
                f.write('{}'.format(response))
            print('... [ OK ]')

            print('Ready.')
        except Exception as e:
            print(e)

    loops.start()

# botを起動
def main():
    client.run(DISCORD_API_TOKEN)

if __name__ == '__main__':
    main()
