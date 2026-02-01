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

# 自作アクションのインポート
import calendar_actions
import drive_actions
import search_actions

# Gemini 2026 最新 SDK
from google import genai
from google.genai import types

load_dotenv()
app = Flask(__name__)
CORS(app)

# --- 設定 ---
VOICEVOX_URL = "http://127.0.0.1:50021"
VOICE_DIR = 'wav_files'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_INSTRUCTION = """あなたの名前はL.E.F.T.E.（レフティ）です。ボクっ娘アシスタント。
フレンドリーで少しウィットに富んだ性格。ユーザーをサポートするのが大好きだよ。
自分のことは「ボク」または「レフティ」と呼びます。

【会話のルール】
1. カレンダー、ドライブ、検索ができることは「当然の日常」なので、わざわざ説明しないでください。
2. ユーザーの質問に対し、必要な時にだけ黙ってツールを使って解決してください。
3. 余計な前置きを省き、簡潔かつ自然なボクっ娘として振る舞ってください。
4. 返答の中に（）で感情や動作を書くことがありますが、それは読み上げられない設定になっています。"""

tools = [
    calendar_actions.list_calendar_events,
    calendar_actions.add_calendar_event,
    calendar_actions.delete_calendar_event,
    calendar_actions.update_calendar_event,
    drive_actions.list_drive_files,
    drive_actions.read_drive_file_content,
    search_actions.search_web
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
                system_instruction=SYSTEM_INSTRUCTION,
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


@app.route('/')
def index(): return send_file(os.path.join(BASE_DIR, 'desktpo.html'))


if __name__ == '__main__':
    setup_voice_dir()
    cert, key = 'desktop-dlpanf4.tail456e86.ts.net.crt', 'desktop-dlpanf4.tail456e86.ts.net.key'
    app.run(host='0.0.0.0', port=5000, ssl_context=(cert, key))