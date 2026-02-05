import winreg
import sys
import os
import urllib.parse
import ctypes  # 先頭で1回だけインポート

# launch_app 関数
def launch_app(url):
    import ctypes
    # 🚀 1. そもそもOSから何を受け取ったか、即座に表示させる
    ctypes.windll.user32.MessageBoxW(0, f"受信した生データ:\n{url}", "DEBUG 1", 64)

    path = url.replace("lefte-launch://", "").rstrip("/")
    path = urllib.parse.unquote(path)

    # 🚀 2. 加工後のパスを表示させる
    if len(path) > 1 and path[1] == '/' and path[0].isalpha():
        path = path[0] + ":" + path[1:]

    clean_path = os.path.normpath(path)
    ctypes.windll.user32.MessageBoxW(0, f"最終的なパス:\n{clean_path}", "DEBUG 2", 64)

    # 🚀 3. 起動を試みる
    try:
        os.startfile(clean_path)
    except Exception as e:
        ctypes.windll.user32.MessageBoxW(0, f"起動エラー:\n{str(e)}", "DEBUG ERROR", 16)
# セットアップ処理
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