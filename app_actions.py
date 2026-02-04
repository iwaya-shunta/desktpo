import sqlite3
import os

DB_NAME = 'chat_history.db'

def init_apps_table():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS apps
                 (id INTEGER PRIMARY KEY, app_name TEXT UNIQUE, exe_path TEXT)''')
    conn.commit()
    conn.close()

def register_app(app_name: str, exe_path: str):
    """新しいアプリをDBに登録します。例: app_name='メモ帳', exe_path='C:/Windows/notepad.exe'"""
    init_apps_table()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO apps (app_name, exe_path) VALUES (?, ?)", (app_name, exe_path))
    conn.commit()
    conn.close()
    return f"了解だよ！『{app_name}』を登録したから、いつでも起動できるよ。"

def launch_app(app_name: str):
    """指定されたアプリ名から、Windows側で実行するためのカスタムURLを返します。"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT exe_path FROM apps WHERE app_name = ?", (app_name,))
    row = c.fetchone()
    conn.close()
    if row:
        return f"🚀LAUNCH_SIGNAL:lefte-launch://{row[0]}"
    return f"ごめんね、『{app_name}』はまだ登録されていないみたい。"

init_apps_table()