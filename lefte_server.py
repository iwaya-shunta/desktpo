import json
import re
import os.path
import datetime
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
import google.generativeai as genai
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()
app = Flask(__name__)
CORS(app)

# 1. 権限設定（カレンダーとドライブの読み書き）
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/drive.readonly'
]

# 2. Gemini の初期設定
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
generation_config = {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 1024,
}

from google.generativeai.types import HarmCategory, HarmBlockThreshold

safety_settings = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
}

model = genai.GenerativeModel(
    model_name="gemini-3-flash-preview",
    generation_config=generation_config,
    safety_settings=safety_settings,
    system_instruction="""あなたはL.E.F.T.E.（レフティ）です。ボクっ娘で快活なアシスタント。親友のように接してね。
予定を追加したい場合は、回答の最後に必ず以下の形式のJSONを1行で含めてください。
{"action": "add_calendar", "summary": "予定名", "start": "ISO日時", "end": "ISO日時"}
日時は2026年基準で、時間は必ず 'T10:00:00' のような形式にしてね。"""
)

chat_session = model.start_chat(history=[])


def get_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


@app.route('/chat', methods=['POST'])
def chat():
    global chat_session
    user_input = request.json.get('message')
    creds = get_credentials()

    # --- 1. 情報収集 (Read) ---
    # 日本時間での正確な「今」を取得
    now_jst = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    now_iso = now_jst.isoformat()

    # カレンダー取得
    service_cal = build('calendar', 'v3', credentials=creds)
    events = service_cal.events().list(calendarId='primary', timeMin=now_iso, maxResults=5, singleEvents=True,
                                       orderBy='startTime').execute().get('items', [])
    cal_data = "\n".join(
        [f"- {e.get('summary')} ({e.get('start').get('dateTime', e.get('start').get('date'))})" for e in
         events]) or "予定なし"

    # ★ドライブの最新ファイル取得（復活させました！）
    service_drive = build('drive', 'v3', credentials=creds)
    files = service_drive.files().list(pageSize=5, fields="files(name, modifiedTime)").execute().get('files', [])
    drive_data = "\n".join([f"- {f.get('name')} (更新: {f.get('modifiedTime')})" for f in files]) or "ファイルなし"

    # --- 2. Geminiに問いかける ---
    prompt = f"""【現在の日時】: {now_jst.strftime('%Y-%m-%d %H:%M')}
【カレンダー】:
{cal_data}
【ドライブ】:
{drive_data}

ユーザー: {user_input}"""

    response = chat_session.send_message(prompt)
    response_text = response.text

    # --- 3. 操作命令の実行 (Write) ---
    if '"action": "add_calendar"' in response_text:
        try:
            json_match = re.search(r'\{"action": "add_calendar".*?\}', response_text)
            if json_match:
                event_data = json.loads(json_match.group())
                event = {
                    'summary': event_data['summary'],
                    'start': {'dateTime': event_data['start'], 'timeZone': 'Asia/Tokyo'},
                    'end': {'dateTime': event_data['end'], 'timeZone': 'Asia/Tokyo'},
                }
                service_cal.events().insert(calendarId='primary', body=event).execute()

                # 登録成功後、ボクに報告させる
                confirm_msg = f"（システム：予定「{event_data['summary']}」をGoogleカレンダーに登録したよ。報告して！）"
                response_text = chat_session.send_message(confirm_msg).text
        except Exception as e:
            print(f"書き込みエラー: {e}")

    return jsonify({"response": response_text})


if __name__ == '__main__':
    app.run(port=5000)