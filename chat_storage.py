import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, 'chat_history.db')

def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        # timestamp の DEFAULT 指定をあえて外して、Pythonから入れるようにします
        c.execute('''CREATE TABLE IF NOT EXISTS messages
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      role TEXT,
                      content TEXT,
                      timestamp TEXT)''')
        conn.commit()
        conn.close()
        print(f"✅ DB初期化完了: {DB_NAME}")
    except Exception as e:
        print(f"❌ DB初期化エラー: {e}")

def save_message(role, content):
    if not content: return
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        # 🚀 保存する時間を Python 側で生成（YYYY-MM-DD HH:MM:SS）
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 明示的に timestamp も保存する
        c.execute("INSERT INTO messages (role, content, timestamp) VALUES (?, ?, ?)",
                  (role, content, now))
        conn.commit()
        conn.close()
        print(f"💾 Saved {role}: {content[:15]}... (Time: {now})")
    except Exception as e:
        print(f"❌ 保存エラー: {e}")

def get_today_history():
    """本日の履歴を取得（Python側で生成した時間で検索）"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        # Python 側で今日の日付を取得
        today_str = datetime.now().strftime('%Y-%m-%d')

        # 🚀 timestamp, role, content の順番で取得（lefte_server.py の r[1], r[2] に合わせる）
        c.execute('''SELECT timestamp, role, content FROM messages
                     WHERE timestamp LIKE ?
                     ORDER BY id ASC''', (f'{today_str}%',))

        rows = c.fetchall()

        # --- 超重要：もし0件なら「形式が違う古いデータ」があるかチェックするデバッグ ---
        if len(rows) == 0:
            c.execute('SELECT timestamp FROM messages ORDER BY id DESC LIMIT 1')
            last = c.fetchone()
            if last:
                print(f"⚠️ 検索失敗！DB内の最新データの形式は: '{last[0]}' ですが、探したのは '{today_str}' です。")
        else:
            print(f"📂 履歴読込: {len(rows)}件取得成功！")

        conn.close()
        return rows
    except Exception as e:
        print(f"❌ 読込エラー: {e}")
        return []