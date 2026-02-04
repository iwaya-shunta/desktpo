import os
import re
import requests
import base64
import time
import glob
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# 🚀 参照エラーを防ぐため、モジュール名だけでインポート
import chat_storage
import app_actions
import calendar_actions
import drive_actions
import search_actions
import gmail_actions

from google import genai
from google.genai import types

load_dotenv()
app = Flask(__name__, static_url_path='', static_folder='static')
CORS(app)

# --- 設定 ---
VOICEVOX_URL = os.getenv("VOICEVOX_URL", "http://127.0.0.1:50021")
VOICE_DIR = 'wav_files'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

chat_storage.init_db()

FUNCTIONAL_RULES = """
1. カレンダー等は「当然の日常」として使い、説明不要。
2. 簡潔に回答せよ。
3. アプリを起動する際は、ツールが返した '🚀LAUNCH_SIGNAL:...' という文字列を必ず回答に含めること。
"""

tools = [
    calendar_actions.list_calendar_events,
    calendar_actions.add_calendar_event,
    calendar_actions.delete_calendar_event,
    calendar_actions.update_calendar_event,
    drive_actions.list_drive_files,
    drive_actions.read_drive_file_content,
    gmail_actions.list_recent_emails,
    search_actions.search_web,
    app_actions.register_app,
    app_actions.launch_app
]


# --- ヘルパー関数 ---
def get_system_instruction():
    personality_path = os.getenv("PERSONALITY_FILE", "personality.txt")
    user_name = os.getenv("USER_NAME", "ユーザー")
    if os.path.exists(personality_path):
        with open(personality_path, "r", encoding="utf-8") as f:
            personality = f.read()
    else:
        personality = "ボクっ娘アシスタントだよ。"
    return f"あなたは {user_name} のアシスタントです。\n{personality}\n{FUNCTIONAL_RULES}"


def generate_voice(text, speaker_id=8, filename="response.wav"):
    clean_text = re.sub(r'\(.*?\)|（.*?）', '', text)
    if not clean_text.strip(): clean_text = "了解だよ。"
    try:
        res = requests.post(f"{VOICEVOX_URL}/audio_query", params={'text': clean_text, 'speaker': speaker_id})
        data = res.json()
        data.update({'speedScale': 1.15, 'intonationScale': 1.4})
        res_syn = requests.post(f"{VOICEVOX_URL}/synthesis", params={'speaker': speaker_id}, json=data)
        with open(filename, "wb") as f:
            f.write(res_syn.content)
    except:
        pass


# --- API ルート ---

@app.route('/history', methods=['GET'])
def history():
    rows = chat_storage.get_today_history()
    return jsonify([{"role": r[1], "content": r[2]} for r in rows])


@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message', '')
    image_b64 = data.get('image')
    mime_type = data.get('mime_type')
    # モデル名は安定版を指定
    model_id = data.get('model', 'gemini-2.0-flash-exp')

    # 🚀 参照エラーを防ぐため、モジュール名.関数名 で統一
    chat_storage.save_message('user', user_input)

    try:
        # 🚀 ここもモジュール名から呼び出し
        past_rows = chat_storage.get_all_history()
        contents = []
        for row in past_rows[-10:]:
            role = "user" if row[1] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": row[2]}]})

        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        current_user_parts = [{"text": f"【現在時刻: {now_str}】\n{user_input}"}]

        # 🚀 型エラーを回避するため辞書形式で追加
        if image_b64:
            current_user_parts.append({
                "inline_data": {"mime_type": mime_type, "data": image_b64}
            })

        contents.append({"role": "user", "parts": current_user_parts})

        response = client.models.generate_content(
            model=model_id,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=get_system_instruction(),
                tools=tools,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
            )
        )

        full_text = response.text or "完了だよ。"
        launch_url = None

        # 🚀 ツール(launch_app)の実行結果から信号を探し出すロジックを追加
        for candidate in response.candidates:
            for part in candidate.content.parts:
                # ツールが返した信号を直接チェック
                if hasattr(part, 'function_response') and part.function_response:
                    res_val = part.function_response.response.get('result', '')
                    if isinstance(res_val, str) and "🚀LAUNCH_SIGNAL:" in res_val:
                        launch_url = res_val.split("🚀LAUNCH_SIGNAL:")[1].strip()
                # 万が一テキストに含まれていた場合も想定
                elif hasattr(part, 'text') and part.text and "🚀LAUNCH_SIGNAL:" in part.text:
                    launch_url = part.text.split("🚀LAUNCH_SIGNAL:")[1].strip()

        # 表示用テキストから信号を隠す
        if launch_url and "🚀LAUNCH_SIGNAL:" in full_text:
            full_text = full_text.split("🚀LAUNCH_SIGNAL:")[0].strip()

        chat_storage.save_message('assistant', full_text)

        voice_filename = f"voice_{int(time.time())}.wav"
        save_path = os.path.join(BASE_DIR, VOICE_DIR, voice_filename)
        generate_voice(full_text, filename=save_path)

        # 🚀 launch_url を JSON に含めて返すように変更
        return jsonify({
            "response": full_text,
            "voice_url": f"/{VOICE_DIR}/{voice_filename}",
            "launch_url": launch_url
        })

    except Exception as e:
        print(f"Chat Error: {e}")
        return jsonify({"response": f"エラーになっちゃった：{str(e)}"})


@app.route(f'/{VOICE_DIR}/<filename>')
def serve_wav(filename):
    return send_from_directory(os.path.join(BASE_DIR, VOICE_DIR), filename)


@app.route('/')
def index():
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    # staticフォルダではなく、ルートにある desktpo.html を読み込む
    with open(os.path.join(BASE_DIR, 'desktpo.html'), 'r', encoding='utf-8') as f:
        html_content = f.read()
    return html_content.replace("YOUR_CALENDAR_ID_HERE", calendar_id)


# 🚀 HTTPS で起動するための処理
if __name__ == '__main__':
    # .env から証明書と鍵のファイル名を取得
    cert_file = os.getenv("CERT_FILE")
    key_file = os.getenv("KEY_FILE")

    # 証明書ファイルが存在する場合のみ HTTPS で起動
    if cert_file and key_file and os.path.exists(cert_file) and os.path.exists(key_file):
        print(f"🔒 HTTPS モードで起動します: {cert_file}")
        app.run(
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", 5000)),
            ssl_context=(cert_file, key_file) # 👈 これが HTTPS 化の心臓部です
        )
    else:
        print("⚠️ 証明書が見つからないため、HTTP モードで起動します。")
        app.run(
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", 5000))
        )