# windows_launcher_setup.py
import winreg
import sys
import sqlite3
import os
import urllib.parse
import ctypes

# 🚀 DBの場所を絶対パスで指定（サーバーと同じ場所を指すように）
DB_PATH = r"C:\Users\iwaya\Documents\htt\chat_history.db"


def launch_app(url):
    # 1. 名前を抽出 (lefte-launch://メモ帳 -> メモ帳)
    app_name = urllib.parse.unquote(url.replace("lefte-launch://", "").rstrip("/"))

    # 2. DBから本当のパスを引く
    # 🚀 DBの絶対パスを指定してください
    DB_PATH = r"C:\Users\iwaya\Documents\htt\chat_history.db"

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT exe_path FROM apps WHERE app_name = ?", (app_name,))
        row = c.fetchone()
        conn.close()

        if row:
            # 3. 本物のパスで起動！
            os.startfile(os.path.normpath(row[0]))
        else:
            ctypes.windll.user32.MessageBoxW(0, f"『{app_name}』は未登録です", "Error", 16)
    except Exception as e:
        ctypes.windll.user32.MessageBoxW(0, f"エラー:\n{str(e)}", "DEBUG ERROR", 16)


def setup():
    executable = sys.executable
    script_path = os.path.abspath(__file__)
    command = f'"{executable}" "{script_path}" "%1"'

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\lefte-launch") as key:
        winreg.SetValue(key, "", winreg.REG_SZ, "URL:L.E.F.T.E. Launcher")
        winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
        with winreg.CreateKey(key, r"shell\open\command") as cmd_key:
            winreg.SetValue(cmd_key, "", winreg.REG_SZ, command)
    print("✅ レジストリ登録を更新しました！")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        launch_app(sys.argv[1])
    else:
        setup()
        input("Enterで終了...")