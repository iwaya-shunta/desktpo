import winreg
import sys
import os
import urllib.parse
import ctypes
import subprocess
from datetime import datetime


# ログと起動の処理
def launch_app(url):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(base_dir, "lefte_debug.log")

    try:
        # 1. プロトコル部分を除去
        path = url.replace("lefte-launch://", "").rstrip("/")
        path = urllib.parse.unquote(path)

        # 🚀【ここが重要】ドライブ文字の後のコロンを復活させる処理
        # 先頭が「C/Windows」のようになっている場合、「C:/Windows」に直す
        if len(path) > 1 and path[1] == '/' and path[0].isalpha():
            path = path[0] + ":" + path[1:]
        elif len(path) > 0 and path[0].isalpha() and ":" not in path:
            # 先頭がアルファベットでコロンがない場合、先頭の直後に挿入
            path = path[0] + ":" + (path[1:] if path[1] == '/' else "/" + path[1:])

        # 2. パスを Windows 形式に正規化（/ を \ に変換）
        clean_path = os.path.normpath(path)

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()}: Launch Request -> {clean_path}\n")

        # 3. 起動実行
        if os.path.exists(clean_path):
            os.startfile(clean_path)
        else:
            ctypes.windll.user32.MessageBoxW(0, f"エラー：ファイルが見つかりません\n{clean_path}", "L.E.F.T.E. Error",
                                             16)

    except Exception as e:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"🔥 Error: {str(e)}\n")


# セットアップ処理
def setup():
    executable = sys.executable
    script_path = os.path.abspath(__file__)
    # 引用符のミスを防ぐためのフォーマット
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