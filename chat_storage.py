import sqlite3
from datetime import datetime

# データベースのファイル名
DB_NAME = 'chat_history.db'


def init_db():
    """データベースとテーブルの初期化"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # messagesテーブルを作成（存在しない場合のみ）
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS messages
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       role
                       TEXT
                       NOT
                       NULL, -- 'user' または 'assistant'
                       content
                       TEXT
                       NOT
                       NULL, -- 発言内容
                       timestamp
                       DATETIME
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   ''')
    conn.commit()
    conn.close()
    print("Database initialized.")


def save_message(role, content):
    """メッセージをデータベースに保存"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        # SQLインジェクションを防ぐため、値を直接入れず '?' を使用します
        cursor.execute(
            'INSERT INTO messages (role, content) VALUES (?, ?)',
            (role, content)
        )
        conn.commit()
        conn.close()
        print(f"Saved: [{role}] {content[:20]}...")
    except Exception as e:
        print(f"Error saving message: {e}")


def get_all_history():
    """全履歴を取得（デバッグ用）"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT timestamp, role, content FROM messages ORDER BY timestamp ASC')
    history = cursor.fetchall()
    conn.close()
    return history

# chat_storage.py の末尾付近に追加
def get_today_history():
    """今日の日付の履歴だけを取得します。"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        # SQLの date関数を使って、今日（localtime）のデータだけを抽出
        cursor.execute('''
            SELECT timestamp, role, content FROM messages 
            WHERE date(timestamp, 'localtime') = date('now', 'localtime') 
            ORDER BY timestamp ASC
        ''')
        history = cursor.fetchall()
        conn.close()
        return history
    except Exception as e:
        print(f"Error fetching today history: {e}")
        return []

# スクリプトを直接実行した時のテスト動作
if __name__ == '__main__':
    init_db()
    save_message('user', 'テストメッセージです')
    save_message('assistant', '保存成功！')

    print("\n--- 現在の履歴 ---")
    for row in get_all_history():
        print(f"{row[0]} | {row[1]}: {row[2]}")