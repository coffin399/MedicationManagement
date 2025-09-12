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
import json
import calendar

# --- 設定ファイルの確認と読み込み ---
CONFIG_FILE = 'config.yaml'
DEFAULT_CONFIG_FILE = 'config-default.yaml'

if not os.path.exists(CONFIG_FILE):
    print(f"設定ファイル '{CONFIG_FILE}' が見つかりません。プログラムを終了します。")
    sys.exit()

with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# Discord設定
TOKEN = config.get('token')
CHANNEL_ID = config.get('channel_id')
TARGET_USERS = config.get('target_users', [])
MESSAGE = config.get('message')
STATUS_MESSAGE = config.get('status_message')
NOTIFY_TIMES_STR = config.get('notify_times', [])

# Gemini設定
GEMINI_API_KEY = config.get('gemini_api_key')
GEMINI_MODEL_NAME = config.get('gemini_model_name', 'gemini-pro')
SYSTEM_PROMPT = config.get('system_prompt')

# GIF設定
GIF_URLS = config.get('gif_urls', [])

# 服薬記録ファイルの設定
MEDICATION_LOG_FILE = 'medication_log.json'

# --- 必須設定のチェック ---
if not TOKEN or TOKEN == "YOUR_DISCORD_BOT_TOKEN":
    print(f"'{CONFIG_FILE}' にDiscord BOTのトークンが設定されていません。")
    sys.exit()
if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
    print(f"'{CONFIG_FILE}' にGemini APIキーが設定されていません。")
    sys.exit()
if not TARGET_USERS or not isinstance(TARGET_USERS, list):
    print(f"'{CONFIG_FILE}' に管理対象のユーザー 'target_users' が正しく設定されていません。")
    sys.exit()

# --- Geminiの初期設定 ---
try:
    genai.configure(api_key=GEMINI_API_KEY)
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


# --- 服薬記録を管理するヘルパー関数 ---
def load_medication_log():
    if not os.path.exists(MEDICATION_LOG_FILE):
        return {}
    try:
        with open(MEDICATION_LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_medication_log(log_data):
    with open(MEDICATION_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)


def generate_calendar_string(year, month, user_id):
    today = datetime.datetime.now(JST).date()
    all_logs = load_medication_log()
    user_log = all_logs.get(str(user_id), {})
    cal = calendar.Calendar(firstweekday=6)
    header = "日 月 火 水 木 金 土\n"
    body = ""
    for week in cal.monthdatescalendar(year, month):
        week_str = []
        for day in week:
            if day.month != month:
                week_str.append("    ")
                continue
            day_str_key = day.strftime("%Y-%m-%d")
            day_num_str = f"{day.day: >2}"
            if user_log.get(day_str_key):
                week_str.append(f"✅{day_num_str}")
            elif day == today:
                week_str.append(f"🗓️{day_num_str}")
            elif day < today:
                week_str.append(f"⚠️{day_num_str}")
            else:
                week_str.append(f"  {day_num_str}")
        body += " ".join(week_str) + "\n"
    return header + body


async def generate_gemini_message():
    try:
        prompt = "さあ、先生への今日のメッセージを一言お願いします。"
        response = await gemini_model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        print(f"Geminiからの応答生成中にエラーが発生しました: {e}")
        return "（ごめんなさい、先生。今日はうまく言葉が出てきません...でも、ちゃんとお薬は飲んでくださいね。）"


# --- [新設] 定期通知と手動通知で共有するロジック ---
async def send_group_notification(channel: discord.TextChannel):
    """未服薬ユーザーにグループ通知を送信する共通関数"""
    all_logs = load_medication_log()
    today = datetime.datetime.now(JST)
    today_str = today.strftime("%Y-%m-%d")

    users_to_notify = []
    for user_info in TARGET_USERS:
        user_id = user_info.get('id')
        if not user_id:
            continue
        user_log = all_logs.get(str(user_id), {})
        if not user_log.get(today_str):
            try:
                user = await bot.fetch_user(user_id)
                if user:
                    users_to_notify.append(user)
            except discord.NotFound:
                print(f"エラー: ユーザーID {user_id} が見つかりません。スキップします。")

    if not users_to_notify:
        return False  # 通知対象がいなかったので False を返す

    try:
        mentions = ' '.join(u.mention for u in users_to_notify)
        user_names_for_log = ', '.join(u.name for u in users_to_notify)
        gemini_sermon = await generate_gemini_message()
        gif_to_send = random.choice(GIF_URLS) if GIF_URLS else ""
        full_message = f'{mentions} {MESSAGE}\n\n{gemini_sermon}\n\n{gif_to_send}'

        embeds_to_send = []
        for user in users_to_notify:
            calendar_str = generate_calendar_string(today.year, today.month, user.id)
            embed = discord.Embed(title=f"{user.display_name}さんのカレンダー", color=discord.Color.orange())
            embed.add_field(name=f"{today.year}年{today.month}月", value=f"```{calendar_str}```")
            embeds_to_send.append(embed)

        await channel.send(content=full_message.strip(), embeds=embeds_to_send[:10])
        print(f"[{today.strftime('%H:%M')}] {user_names_for_log} さんに共通のメッセージとカレンダーを送信しました。")
        return True  # 通知を送信したので True を返す
    except Exception as e:
        print(f"共通メッセージ送信中にエラーが発生しました: {e}")
        return False


# --- [変更] 共通関数を呼び出すように修正 ---
@tasks.loop(minutes=1)
async def reminder():
    await bot.wait_until_ready()
    now = datetime.datetime.now(JST).time()
    is_notify_time = any(now.hour == nt.hour and now.minute == nt.minute for nt in notify_times)

    if is_notify_time:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            await send_group_notification(channel)
        else:
            print(f"エラー: チャンネルID {CHANNEL_ID} が見つかりません。")


# --- [新設] 全員に通知を送信するコマンド ---
@tree.command(name="notice", description="未服薬のユーザー全員に、公開の通知を送信します。")
async def notice(interaction: discord.Interaction):
    try:
        # コマンドの実行に時間がかかることをDiscordに伝える
        await interaction.response.defer(ephemeral=True)

        # 共通関数を呼び出して通知を送信
        sent = await send_group_notification(interaction.channel)

        # 実行者に結果をフィードバック（本人にだけ見える）
        if sent:
            await interaction.followup.send("未服薬のユーザーに通知を送信しました。", ephemeral=True)
        else:
            await interaction.followup.send("全員が服薬済みのため、通知は送信しませんでした。", ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"コマンド実行中にエラーが発生しました: {e}", ephemeral=True)


@tree.command(name="test_notice", description="あなただけにテスト通知を送信します。")
async def test_notice(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=True)
        gemini_sermon = await generate_gemini_message()
        gif_to_send = random.choice(GIF_URLS) if GIF_URLS else ""
        full_message = f"【テスト通知】\n{interaction.user.mention} {MESSAGE}\n\n{gemini_sermon}\n\n{gif_to_send}"
        today = datetime.datetime.now(JST)
        calendar_str = generate_calendar_string(today.year, today.month, interaction.user.id)
        embed = discord.Embed(title=f"{interaction.user.display_name}さんの現在のカレンダー",
                              color=discord.Color.blue())
        embed.add_field(name=f"{today.year}年{today.month}月", value=f"```{calendar_str}```")
        embed.set_footer(text="これはあなたにだけ表示されているテスト通知です。")
        await interaction.followup.send(content=full_message.strip(), embed=embed)
    except Exception as e:
        await interaction.followup.send(f"コマンド実行中にエラーが発生しました: {e}", ephemeral=True)


@tree.command(name="check", description="指定したユーザーの服薬状況をカレンダーで確認します。")
@app_commands.describe(user="状況を確認するユーザーを選択してください。")
async def check(interaction: discord.Interaction, user: discord.Member):
    try:
        await interaction.response.defer()
        today = datetime.datetime.now(JST)
        today_str = today.strftime("%Y-%m-%d")
        all_logs = load_medication_log()
        user_log = all_logs.get(str(user.id), {})
        if user_log.get(today_str):
            description_text = f"**{user.display_name}** さんは今日のお薬はもう飲みましたね！えらい！"
            embed_color = discord.Color.green()
        else:
            description_text = f"**{user.display_name}** さんは今日のお薬はまだのようです。忘れないでくださいね。"
            embed_color = discord.Color.orange()
        calendar_str = generate_calendar_string(today.year, today.month, user.id)
        embed = discord.Embed(title=f"{user.display_name}さんの服薬カレンダー", description=description_text,
                              color=embed_color)
        embed.add_field(name=f"{today.year}年{today.month}月", value=f"```{calendar_str}```")
        embed.set_footer(text="🗓️:今日 ✅:飲んだ日 ⚠️:飲み忘れ\n/med で服薬したことにする")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"コマンド実行中にエラーが発生しました: {e}", ephemeral=True)


@tree.command(name="med", description="指定したユーザーがお薬を飲んだことを記録します。")
@app_commands.describe(user="お薬を飲んだユーザーを選択してください。")
async def med(interaction: discord.Interaction, user: discord.Member):
    try:
        today = datetime.datetime.now(JST)
        today_str = today.strftime("%Y-%m-%d")
        all_logs = load_medication_log()
        user_id_str = str(user.id)
        user_log = all_logs.get(user_id_str, {})
        user_log[today_str] = True
        all_logs[user_id_str] = user_log
        save_medication_log(all_logs)
        calendar_str = generate_calendar_string(today.year, today.month, user.id)
        embed = discord.Embed(title=f"{user.display_name}さん、よくできました！",
                              description="ちゃんとお薬が飲めてえらいです！\nカレンダーを更新しました。",
                              color=discord.Color.green())
        embed.add_field(name=f"{today.year}年{today.month}月", value=f"```{calendar_str}```")
        embed.set_footer(text="🗓️:今日 ✅:飲んだ日 ⚠️:飲み忘れ")
        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"コマンド実行中にエラーが発生しました: {e}", ephemeral=True)


@tree.command(name="uncheck", description="指定したユーザーの今日の服薬記録を取り消します。")
@app_commands.describe(user="記録を取り消すユーザーを選択してください。")
async def uncheck(interaction: discord.Interaction, user: discord.Member):
    try:
        today = datetime.datetime.now(JST)
        today_str = today.strftime("%Y-%m-%d")
        all_logs = load_medication_log()
        user_id_str = str(user.id)
        user_log = all_logs.get(user_id_str, {})
        if today_str in user_log:
            del user_log[today_str]
            all_logs[user_id_str] = user_log
            save_medication_log(all_logs)
            description_text = f"**{user.display_name}** さんの今日のお薬の記録を取り消しました。"
            embed_color = discord.Color.orange()
        else:
            description_text = f"**{user.display_name}** さんは今日はまだ服薬記録がありませんでした。"
            embed_color = discord.Color.blue()
        calendar_str = generate_calendar_string(today.year, today.month, user.id)
        embed = discord.Embed(title="服薬記録の取り消し", description=description_text, color=embed_color)
        embed.add_field(name=f"{today.year}年{today.month}月", value=f"```{calendar_str}```")
        embed.set_footer(text="🗓️:今日 ✅:飲んだ日 ⚠️:飲み忘れ")
        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"コマンド実行中にエラーが発生しました: {e}", ephemeral=True)


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


bot.run(TOKEN)