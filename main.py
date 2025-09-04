# main.py

import discord
from discord import app_commands
from discord.ext import tasks
import yaml
import datetime
import pytz
import os
import sys
import shutil

# --- 設定ファイルの確認と読み込み ---
CONFIG_FILE = 'config.yaml'
DEFAULT_CONFIG_FILE = 'config-default.yaml'

# config.yaml が存在しない場合、config-default.yaml からコピーして生成する
if not os.path.exists(CONFIG_FILE):
    print(f"設定ファイル '{CONFIG_FILE}' が見つかりません。")
    try:
        shutil.copy(DEFAULT_CONFIG_FILE, CONFIG_FILE)
        print(f"'{DEFAULT_CONFIG_FILE}' から '{CONFIG_FILE}' を生成しました。")
        print(f"'{CONFIG_FILE}' を編集して、BOTのトークンなどを設定してから再度起動してください。")
    except FileNotFoundError:
        print(f"エラー: テンプレートファイル '{DEFAULT_CONFIG_FILE}' が見つかりません。")
        print("プログラムを終了します。")
    sys.exit() # 初回は設定を促すためにプログラムを終了する

# 設定ファイルを読み込む
with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 設定ファイルから各値を取得
TOKEN = config.get('token')
CHANNEL_ID = config.get('channel_id')
USER_ID = config.get('user_id')
MESSAGE = config.get('message')
STATUS_MESSAGE = config.get('status_message')

# トークンが設定されているか確認
if not TOKEN or TOKEN == "YOUR_DISCORD_BOT_TOKEN":
    print(f"'{CONFIG_FILE}' にDiscord BOTのトークンが設定されていません。")
    print("トークンを設定してから再度起動してください。")
    sys.exit()

# --- ここから下はBOTのメインロジック ---

# Botのインテントを設定
intents = discord.Intents.default()
intents.members = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# 日本時間(JST)のタイムゾーンを設定
JST = pytz.timezone('Asia/Tokyo')

# 通知を送る時間をリストで指定 (時, 分)
notify_times = [
    datetime.time(hour=9, minute=0, tzinfo=JST),
    datetime.time(hour=12, minute=0, tzinfo=JST),
    datetime.time(hour=14, minute=0, tzinfo=JST),
]

# 1分ごとに時間をチェックして通知を送るタスク
@tasks.loop(minutes=1)
async def reminder():
    await bot.wait_until_ready()
    now = datetime.datetime.now(JST).time()
    for notify_time in notify_times:
        if now.hour == notify_time.hour and now.minute == notify_time.minute:
            try:
                channel = bot.get_channel(CHANNEL_ID)
                if channel:
                    user = await bot.fetch_user(USER_ID)
                    if user:
                        await channel.send(f'{user.mention} {MESSAGE}')
                        print(f"[{now.strftime('%H:%M')}] {user.name}さんにメッセージを送信しました。")
                    else:
                        print(f"エラー: ユーザーID {USER_ID} が見つかりません。")
                else:
                    print(f"エラー: チャンネルID {CHANNEL_ID} が見つかりません。")
            except Exception as e:
                print(f"メッセージ送信中にエラーが発生しました: {e}")
            break

# /notice コマンドの定義
@tree.command(name="notice", description="設定された通知メッセージをテスト表示します。")
async def notice(interaction: discord.Interaction):
    """通知メッセージをテスト表示するコマンド"""
    try:
        user = await bot.fetch_user(USER_ID)
        if user:
            await interaction.response.send_message(f"テスト通知:\n{user.mention} {MESSAGE}")
        else:
            await interaction.response.send_message(f"エラー: ユーザーID `{USER_ID}` が見つかりません。", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"コマンド実行中にエラーが発生しました: {e}", ephemeral=True)

# Botが起動したときに実行されるイベント
@bot.event
async def on_ready():
    print(f'{bot.user} としてログインしました。')
    try:
        game = discord.Game(STATUS_MESSAGE)
        await bot.change_presence(status=discord.Status.online, activity=game)
        print(f"ステータスを「{STATUS_MESSAGE}」に設定しました。")
    except Exception as e:
        print(f"ステータスの設定中にエラーが発生しました: {e}")
    try:
        synced = await tree.sync()
        print(f"{len(synced)}個のコマンドを同期しました。")
    except Exception as e:
        print(f"コマンドの同期中にエラーが発生しました: {e}")
    reminder.start()

# Botを実行
bot.run(TOKEN)