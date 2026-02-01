import os
import re
import requests
import base64
import time
import glob
from datetime import datetime
from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from config import SCOPES

# 自作アクションのインポート
import calendar_actions
import drive_actions
import search_actions
import gmail_actions

# Gemini 2026 最新 SDK
from google import genai
from google.genai import types

load_dotenv()
app = Flask(__name__)
CORS(app)

# --- 設定 ---
VOICEVOX_URL = os.getenv("VOICEVOX_URL", "http://127.0.0.1:50021")
VOICE_DIR = 'wav_files'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

FUNCTIONAL_RULES = """
【会話のルール】
1. カレンダー、ドライブ、検索ができることは「当然の日常」なので、わざわざ説明しないでください。
2. ユーザーの質問に対し、必要な時にだけ黙ってツールを使って解決してください。
3. 余計な前置きを省き、簡潔かつ自然に振る舞ってください。
"""

tools = [
    calendar_actions.list_calendar_events,
    calendar_actions.add_calendar_event,
    calendar_actions.delete_calendar_event,
    calendar_actions.update_calendar_event,
    drive_actions.list_drive_files,
    drive_actions.read_drive_file_content,
    gmail_actions.list_recent_emails,
    search_actions.search_web
]
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/gmail.readonly'  # 👈 これも忘れずに
]

# --- 読み上げ用クリーンアップ ---
def clean_text_for_speech(text):
    """（）や ( ) を読み飛ばすための処理"""
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'（.*?）', '', text)
    return text


def setup_voice_dir():
    path = os.path.join(BASE_DIR, VOICE_DIR)
    if not os.path.exists(path): os.makedirs(path)
    for f in glob.glob(os.path.join(path, "*.wav")): os.remove(f)


def generate_voice(text, speaker_id=8, filename="response.wav"):
    clean_text = clean_text_for_speech(text)
    if not clean_text.strip(): clean_text = "了解だよ。"

    res_query = requests.post(f"{VOICEVOX_URL}/audio_query", params={'text': clean_text, 'speaker': speaker_id})
    query_data = res_query.json()
    query_data.update({'speedScale': 1.15, 'intonationScale': 1.4})
    res_syn = requests.post(f"{VOICEVOX_URL}/synthesis", params={'speaker': speaker_id}, json=query_data)
    with open(filename, "wb") as f: f.write(res_syn.content)


def get_system_instruction():
    # .env から性格ファイルのパスを取得（デフォルトは personality.txt）
    personality_path = os.getenv("PERSONALITY_FILE", "personality.txt")

    # 性格ファイルを読み込む（なければデフォルトの性格を入れる）
    if os.path.exists(personality_path):
        with open(personality_path, "r", encoding="utf-8") as f:
            personality_content = f.read()
    else:
        personality_content = "あなたは優秀なアシスタントです。"

    # 性格と機能を合体させて返す！
    return f"{personality_content}\n{FUNCTIONAL_RULES}"
# --- API ルート ---
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message', '')
    image_b64 = data.get('image')
    mime_type = data.get('mime_type')
    model_id = data.get('model', 'gemini-3-flash-preview')  # フロントから受け取る

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    prompt = f"【現在時刻: {now_str}】\n{user_input}"

    try:
        parts = [prompt]
        if image_b64:
            parts.append(types.Part.from_bytes(data=base64.b64decode(image_b64), mime_type=mime_type))

        response = client.models.generate_content(
            model=model_id,
            contents=parts,
            config=types.GenerateContentConfig(
                system_instruction=get_system_instruction(),
                tools=tools,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
            )
        )

        full_text = response.text or "作業完了だよ！"
        voice_filename = f"voice_{int(time.time())}.wav"
        save_path = os.path.join(BASE_DIR, VOICE_DIR, voice_filename)
        generate_voice(full_text, filename=save_path)

        return jsonify({"response": full_text, "voice_url": f"/{VOICE_DIR}/{voice_filename}"})
    except Exception as e:
        return jsonify({"response": f"ごめんね、エラーになっちゃった：{str(e)}"})


@app.route(f'/{VOICE_DIR}/<filename>')
def serve_wav(filename): return send_from_directory(os.path.join(BASE_DIR, VOICE_DIR), filename)

def get_system_instruction():
    personality_path = os.getenv("PERSONALITY_FILE", "personality.txt")
    # .env からユーザー名を取得（なければ「ユーザー」にする）
    user_name = os.getenv("USER_NAME", "ユーザー")

    if os.path.exists(personality_path):
        with open(personality_path, "r", encoding="utf-8") as f:
            personality_content = f.read()
    else:
        personality_content = "あなたは優秀なアシスタントです。"

    # プロンプトの冒頭で「誰に話しているか」を定義する
    return f"あなたは {user_name} のアシスタントです。\n{personality_content}\n{FUNCTIONAL_RULES}"
@app.route('/')
def index():
    # .env からカレンダーIDを取得（未設定なら primary）
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")

    try:
        # HTMLを読み込んで、IDを置換してからブラウザに返す
        with open(os.path.join(BASE_DIR, 'desktpo.html'), 'r', encoding='utf-8') as f:
            html_content = f.read()

        # HTML内の placeholder を .env の値に置き換える
        html_content = html_content.replace("YOUR_CALENDAR_ID_HERE", calendar_id)

        return html_content
    except Exception as e:
        return f"HTML読み込みエラー: {str(e)}"


# --- lefte_server.py の末尾を修正 ---
if __name__ == '__main__':
    setup_voice_dir()

    # .env から設定を読み込む
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))  # ポートは数値にする必要があるよ
    cert = os.getenv("CERT_FILE")
    key = os.getenv("KEY_FILE")

    if cert and key and os.path.exists(cert):
        print(f"🔒 HTTPS モードで起動します: {cert}")
        app.run(host=host, port=port, ssl_context=(cert, key))
    else:
        print(f"⚠️ HTTP モードで起動します ({host}:{port})")
        app.run(host=host, port=port)