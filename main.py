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

if not os.path.exists(CONFIG_FILE):
    print(f"設定ファイル '{CONFIG_FILE}' が見つかりません。")
    try:
        shutil.copy(DEFAULT_CONFIG_FILE, CONFIG_FILE)
        print(f"'{DEFAULT_CONFIG_FILE}' から '{CONFIG_FILE}' を生成しました。")
        print(f"'{CONFIG_FILE}' を編集して、BOTのトークンなどを設定してから再度起動してください。")
    except FileNotFoundError:
        print(f"エラー: テンプレートファイル '{DEFAULT_CONFIG_FILE}' が見つかりません。")
        print("プログラムを終了します。")
    sys.exit()

with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

TOKEN = config.get('token')
CHANNEL_ID = config.get('channel_id')
USER_ID = config.get('user_id')
MESSAGE = config.get('message')
STATUS_MESSAGE = config.get('status_message')
NOTIFY_TIMES_STR = config.get('notify_times', [])  # 通知時間を文字列のリストとして読み込む

if not TOKEN or TOKEN == "YOUR_DISCORD_BOT_TOKEN":
    print(f"'{CONFIG_FILE}' にDiscord BOTのトークンが設定されていません。")
    print("トークンを設定してから再度起動してください。")
    sys.exit()

# --- ここから下はBOTのメインロジック ---

intents = discord.Intents.default()
intents.members = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# --- 通知時間の設定 ---
JST = pytz.timezone('Asia/Tokyo')
notify_times = []
if isinstance(NOTIFY_TIMES_STR, list):
    for t_str in NOTIFY_TIMES_STR:
        try:
            # "HH:MM"形式の文字列をtimeオブジェクトに変換
            time_obj = datetime.datetime.strptime(t_str, "%H:%M").time()
            # タイムゾーン情報を付与してリストに追加
            notify_times.append(time_obj.replace(tzinfo=JST))
        except (ValueError, TypeError):
            print(
                f"警告: '{CONFIG_FILE}' の notify_times にある '{t_str}' は 'HH:MM' 形式ではありません。この時間は無視されます。")
else:
    print(f"警告: '{CONFIG_FILE}' の notify_times がリスト形式ではありません。定期通知は機能しません。")

if notify_times:
    print(f"通知設定時間 (JST): {[t.strftime('%H:%M') for t in notify_times]}")
else:
    print("警告: 通知時間が一つも設定されていません。")


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

    # 通知時間が設定されている場合のみタスクを開始
    if notify_times:
        reminder.start()


# Botを実行
bot.run(TOKEN)