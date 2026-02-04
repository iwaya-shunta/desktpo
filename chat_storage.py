import sqlite3
from datetime import datetime

DB_NAME = 'chat_history.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  role TEXT,
                  content TEXT,
                  timestamp DATETIME DEFAULT (DATETIME('now', 'localtime')))''')
    conn.commit()
    conn.close()

def save_message(role, content):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO messages (role, content) VALUES (?, ?)", (role, content))
    conn.commit()
    conn.close()

def get_today_history():
    """今日の日付の履歴だけを取得します。"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''SELECT timestamp, role, content FROM messages 
                 WHERE date(timestamp) = date('now', 'localtime') 
                 ORDER BY id ASC''')
    rows = c.fetchall()
    conn.close()
    return rows

# 🚀 この関数が抜けていたので追加します
def get_all_history():
    """すべての履歴を取得します（Geminiの文脈理解に使用）。"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''SELECT timestamp, role, content FROM messages 
                 ORDER BY id ASC''')
    rows = c.fetchall()
    conn.close()
    return rows