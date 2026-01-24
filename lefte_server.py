import calendar_actions
import os.path
import drive_actions
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
import google.generativeai as genai
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

load_dotenv()
app = Flask(__name__)
CORS(app)

# 1. 権限設定（カレンダーとドライブの読み書き）
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/drive.readonly'
]

tools_list = [
    calendar_actions.list_calendar_events,
    calendar_actions.add_calendar_event,
    calendar_actions.delete_calendar_event,
    calendar_actions.update_calendar_event,
    drive_actions.list_drive_files,       # 追加！
    drive_actions.read_drive_file_content
]

# 2. Gemini の初期設定
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
generation_config = {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 1024,
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_ONLY_HIGH",
    },
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_ONLY_HIGH",
    },
]

# --- 50行目付近のモデル設定も、警告が出ない形に修正 ---
model = genai.GenerativeModel(
    model_name="gemini-3-flash-preview",
    generation_config={
        "temperature": 0.9,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 1024,
    },
    safety_settings=safety_settings, # ここに修正したリストを渡す
    tools=tools_list,
    system_instruction="""あなたはL.E.F.T.E.です。ボクっ娘アシスタント。
ユーザーの依頼に合わせてカレンダー関数を使い分けてね。
実行後は結果を見て明るく報告して！"""
)

chat_session = model.start_chat(history=[], enable_automatic_function_calling=True)


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

    try:
        # 1. ボク（Gemini）にメッセージを送信
        response = chat_session.send_message(user_input)

        # 2. もしボクが「実行」だけで満足して喋り足りない（テキストが短い）場合、
        #    もう一度背中を押してあげます
        if not response.text or len(response.text) < 10:
            response = chat_session.send_message("カレンダーの結果を全部教えて！最後までボクっ娘らしく喋ってね！")

        # 3. 複数のパートに分かれている可能性も考えて、念のためテキストを結合
        full_text = "".join([part.text for part in response.parts if part.text])
        latest_events = calendar_actions.list_calendar_events()
        return jsonify({
            "response": full_text,
            "calendar_data": latest_events  # ブラウザに最新データをこっそり教える
        })

    except Exception as e:
        print(f"チャット実行エラー: {e}")
        return jsonify({"response": "ごめんね、カレンダーの操作中にちょっと躓いちゃったみたい。もう一度試してみて！"})


if __name__ == '__main__':
    app.run(port=5000)