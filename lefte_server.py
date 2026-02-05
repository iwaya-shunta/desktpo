import os, re, requests, time
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

import chat_storage
import calendar_actions
import drive_actions
import search_actions
import gmail_actions
import app_actions

from google import genai
from google.genai import types

load_dotenv()
app = Flask(__name__, static_url_path='', static_folder='static')
CORS(app)

VOICEVOX_URL = os.getenv("VOICEVOX_URL", "http://127.0.0.1:50021")
VOICE_DIR = 'wav_files'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 音声フォルダがない場合は作成
if not os.path.exists(os.path.join(BASE_DIR, VOICE_DIR)):
    os.makedirs(os.path.join(BASE_DIR, VOICE_DIR))

FUNCTIONAL_RULES = """
1. カレンダー/ドライブ等は当然の日常として使い、説明は不要。
2. 簡潔に回答せよ。
3. アプリを起動する際は、ツールが返した '🚀LAUNCH_SIGNAL:...' を必ず含めること。
"""

tools = [
    calendar_actions.list_calendar_events, calendar_actions.add_calendar_event,
    calendar_actions.delete_calendar_event, calendar_actions.update_calendar_event,
    drive_actions.list_drive_files, drive_actions.read_drive_file_content,
    gmail_actions.list_recent_emails, search_actions.search_web,
    app_actions.register_app, app_actions.launch_app
]

chat_storage.init_db()


def get_system_instruction():
    """personality.txt から性格設定を読み込む"""
    # .env で指定がない場合は personality.txt を探す
    personality_path = os.getenv("PERSONALITY_FILE", "personality.txt")
    full_path = os.path.join(BASE_DIR, personality_path)

    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            personality = f.read()
    else:
        # ファイルがない場合の予備
        personality = "あなたは助手の L.E.F.T.E. です。"

    return f"{personality}\n{FUNCTIONAL_RULES}"

def generate_voice(text, speaker_id=8, filename="response.wav"):
    clean_text = re.sub(r'\(.*?\)|（.*?）', '', text)
    if not clean_text.strip(): clean_text = "了解だよ。"
    try:
        res = requests.post(f"{VOICEVOX_URL}/audio_query", params={'text': clean_text, 'speaker': speaker_id})
        data = res.json()
        data.update({'speedScale': 1.15, 'intonationScale': 1.4})
        res_syn = requests.post(f"{VOICEVOX_URL}/synthesis", params={'speaker': speaker_id}, json=data)
        with open(filename, "wb") as f: f.write(res_syn.content)
    except Exception as e:
        print(f"Voice generation error: {e}")

@app.route('/wav_files/<filename>')
def serve_wav(filename):
    """音声ファイルを配信するルート（404対策）"""
    return send_from_directory(os.path.join(BASE_DIR, VOICE_DIR), filename)


@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message', '')

    # 1. ユーザーの発言を保存
    chat_storage.save_message('user', user_input)

    try:
        # 文脈作成
        past_rows = chat_storage.get_today_history()
        contents = [{"role": ("user" if r[1] == "user" else "model"), "parts": [{"text": r[2]}]} for r in
                    past_rows[-10:]]
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        contents.append({"role": "user", "parts": [{"text": f"【現在時刻: {now_str}】\n{user_input}"}]})

        # Gemini 呼び出し
        response = client.models.generate_content(
            model=data.get('model', 'gemini-2.0-flash-exp'),
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=get_system_instruction(),
                tools=tools, automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
            )
        )

        full_text = response.text or "完了だよ。"
        launch_url = None

        # 🚀 信号の抜き出しとテキストのクリーニング
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text and "🚀LAUNCH_SIGNAL:" in part.text:
                launch_url = part.text.split("🚀LAUNCH_SIGNAL:")[1].strip()
            elif hasattr(part, 'function_response') and part.function_response:
                res_val = part.function_response.response.get('result', '')
                if isinstance(res_val, str) and "🚀LAUNCH_SIGNAL:" in res_val:
                    launch_url = res_val.split("🚀LAUNCH_SIGNAL:")[1].strip()

        # 表示用テキストから信号を消す
        if launch_url and "🚀LAUNCH_SIGNAL:" in full_text:
            full_text = full_text.split("🚀LAUNCH_SIGNAL:")[0].strip()

        # --- 🚀 ここで AI の返答を 1 回だけ保存！ ---
        chat_storage.save_message('assistant', full_text)
        print(f"DEBUG: AIの返答をDBに書き込みました: {full_text[:15]}...")

        # 音声生成
        voice_filename = f"v_{int(time.time())}.wav"
        save_path = os.path.join(BASE_DIR, VOICE_DIR, voice_filename)
        generate_voice(full_text, filename=save_path)

        return jsonify({
            "response": full_text,
            "voice_url": f"/wav_files/{voice_filename}",
            "launch_url": launch_url
        })

    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({"response": f"エラー：{str(e)}"})

@app.route('/')
def index():
    with open(os.path.join(BASE_DIR, 'desktpo.html'), 'r', encoding='utf-8') as f:
        return f.read().replace("YOUR_CALENDAR_ID_HERE", os.getenv("GOOGLE_CALENDAR_ID", "primary"))

@app.route('/history', methods=['GET'])
def history_api():
    """過去の履歴を取得してフロントに返す"""
    try:
        rows = chat_storage.get_today_history()
        return jsonify([{"role": r[1], "content": r[2]} for r in rows])
    except Exception as e:
        print(f"History error: {e}")
        return jsonify([])

@app.route('/service-worker.js')
def serve_sw():
    """PWA用のサービスワーカーを配信"""
    return send_from_directory(BASE_DIR, 'static/service-worker.js')

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory(BASE_DIR, 'manifest.json')

if __name__ == '__main__':
    cert_file = os.getenv("CERT_FILE")
    key_file = os.getenv("KEY_FILE")
    if cert_file and key_file and os.path.exists(cert_file):
        app.run(host="0.0.0.0", port=5000, ssl_context=(cert_file, key_file))
    else:
        app.run(host="0.0.0.0", port=5000)