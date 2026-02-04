import sqlite3
import os

DB_NAME = 'chat_history.db'


def init_apps_table():
    """アプリ管理用のテーブルを作成する"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS apps
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY,
                     app_name
                     TEXT
                     UNIQUE,
                     exe_path
                     TEXT
                 )''')
    conn.commit()
    conn.close()


def register_app(app_name: str, exe_path: str):
    """
    新しいアプリをDBに登録します。
    例: app_name="メモ帳", exe_path="C:/Windows/notepad.exe"
    """
    init_apps_table()
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO apps (app_name, exe_path) VALUES (?, ?)",
                  (app_name, exe_path))
        conn.commit()
        conn.close()
        return f"了解だよ！『{app_name}』を登録したから、いつでも起動できるよ。"
    except Exception as e:
        return f"登録中にエラーが起きちゃった：{str(e)}"


def launch_app(app_name: str):
    """
    指定されたアプリ名から、Windows側で実行するためのカスタムURLを返します。
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT exe_path FROM apps WHERE app_name = ?", (app_name,))
    row = c.fetchone()
    conn.close()

    if row:
        exe_path = row[0]
        # カスタムプロトコル形式を生成
        protocol_url = f"lefte-launch://{exe_path}"
        # フロントエンド側で location.href を動かすための合図を送る
        return f"🚀LAUNCH_SIGNAL:{protocol_url}"
    else:
        return f"ごめんね、『{app_name}』はまだ登録されていないみたい。"


# 初回実行時にテーブルを作成
init_apps_table()