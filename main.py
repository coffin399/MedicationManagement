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
import random
import google.generativeai as genai

# --- 設定ファイルの確認と読み込み ---
CONFIG_FILE = 'config.yaml'
DEFAULT_CONFIG_FILE = 'config-default.yaml'  # このファイルは今は使いませんが、念のため残しておきます

if not os.path.exists(CONFIG_FILE):
    print(f"設定ファイル '{CONFIG_FILE}' が見つかりません。プログラムを終了します。")
    sys.exit()

with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# Discord設定
TOKEN = config.get('token')
CHANNEL_ID = config.get('channel_id')
USER_ID = config.get('user_id')
MESSAGE = config.get('message')
STATUS_MESSAGE = config.get('status_message')
NOTIFY_TIMES_STR = config.get('notify_times', [])

# Gemini設定
GEMINI_API_KEY = config.get('gemini_api_key')
# config.yamlからモデル名を読み込む。指定がない場合は 'gemini-pro' を使う
GEMINI_MODEL_NAME = config.get('gemini_model_name', 'gemini-pro')
SYSTEM_PROMPT = config.get('system_prompt')

# GIF設定
GIF_URLS = config.get('gif_urls', [])

# --- 必須設定のチェック ---
if not TOKEN or TOKEN == "YOUR_DISCORD_BOT_TOKEN":
    print(f"'{CONFIG_FILE}' にDiscord BOTのトークンが設定されていません。")
    sys.exit()
if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
    print(f"'{CONFIG_FILE}' にGemini APIキーが設定されていません。")
    sys.exit()

# --- Geminiの初期設定 ---
try:
    genai.configure(api_key=GEMINI_API_KEY)
    # configから読み込んだモデル名で初期化する
    gemini_model = genai.GenerativeModel(
        model_name=GEMINI_MODEL_NAME,
        system_instruction=SYSTEM_PROMPT
    )
    print(f"Geminiモデル ({GEMINI_MODEL_NAME}) の初期化に成功しました。")
except Exception as e:
    print(f"Geminiの初期化中にエラーが発生しました: {e}")
    print("APIキーやモデル名が正しいか確認してください。")
    sys.exit()

# --- BOTのメインロジック ---
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
            time_obj = datetime.datetime.strptime(t_str, "%H:%M").time()
            notify_times.append(time_obj.replace(tzinfo=JST))
        except (ValueError, TypeError):
            print(f"警告: '{t_str}' は 'HH:MM' 形式ではありません。無視されます。")
else:
    print(f"警告: 'notify_times' がリスト形式ではありません。定期通知は機能しません。")

if notify_times:
    print(f"通知設定時間 (JST): {[t.strftime('%H:%M') for t in notify_times]}")
else:
    print("警告: 通知時間が一つも設定されていません。")


async def generate_gemini_message():
    """Geminiからメッセージを生成する関数"""
    try:
        prompt = "さあ、先生への今日のメッセージを一言お願いします。"
        response = await gemini_model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        print(f"Geminiからの応答生成中にエラーが発生しました: {e}")
        return "（ごめんなさい、先生。今日はうまく言葉が出てきません...でも、ちゃんとお薬は飲んでくださいね。）"


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
                        gemini_sermon = await generate_gemini_message()

                        gif_to_send = ""
                        if GIF_URLS:
                            gif_to_send = random.choice(GIF_URLS)

                        full_message = f'{user.mention} {MESSAGE}\n\n{gemini_sermon}\n\n{gif_to_send}'
                        await channel.send(full_message.strip())  # 末尾の不要な改行を削除
                        print(f"[{now.strftime('%H:%M')}] {user.name}さんにメッセージを送信しました。")
                    else:
                        print(f"エラー: ユーザーID {USER_ID} が見つかりません。")
                else:
                    print(f"エラー: チャンネルID {CHANNEL_ID} が見つかりません。")
            except Exception as e:
                print(f"メッセージ送信中にエラーが発生しました: {e}")
            break


# /notice コマンドの定義
@tree.command(name="notice", description="Gemini連携とGIF投稿を含む通知をテストします。")
async def notice(interaction: discord.Interaction):
    """通知メッセージをテスト表示するコマンド"""
    try:
        user = await bot.fetch_user(USER_ID)
        if user:
            await interaction.response.defer()
            gemini_sermon = await generate_gemini_message()

            gif_to_send = ""
            if GIF_URLS:
                gif_to_send = random.choice(GIF_URLS)

            full_message = f"【テスト通知】\n{user.mention} {MESSAGE}\n\n{gemini_sermon}\n\n{gif_to_send}"
            await interaction.followup.send(full_message.strip())
        else:
            await interaction.response.send_message(f"エラー: ユーザーID `{USER_ID}` が見つかりません。", ephemeral=True)
    except Exception as e:
        if not interaction.response.is_done():
            await interaction.response.send_message(f"コマンド実行中にエラーが発生しました: {e}", ephemeral=True)
        else:
            await interaction.followup.send(f"コマンド実行中にエラーが発生しました: {e}", ephemeral=True)


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

    if notify_times:
        reminder.start()


# Botを実行
bot.run(TOKEN)