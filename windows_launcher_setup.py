import winreg
import sys
import os
import subprocess
import urllib.parse


def register_protocol():
    """Windowsレジストリに lefte-launch プロトコルを登録する"""
    # このスクリプト自身のパスを取得
    executable = sys.executable
    script_path = os.path.abspath(__file__)
    # 実行コマンド: python.exe "このスクリプト" "引数"
    command = f'"{executable}" "{script_path}" "%1"'

    protocol = "lefte-launch"
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{protocol}") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, "URL:L.E.F.T.E. Launcher")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
            with winreg.CreateKey(key, r"shell\open\command") as cmd_key:
                winreg.SetValue(cmd_key, "", winreg.REG_SZ, command)
        print(f"✅ プロトコル '{protocol}' を登録しました。")
        print(f"実行コマンド: {command}")
    except Exception as e:
        print(f"❌ 登録に失敗しました: {e}")


def launch_app(url):
    """lefte-launch://C:/path/to/exe 形式のURLからアプリを起動する"""
    # プロトコル部分を除去してパスを取り出す
    path = url.replace("lefte-launch://", "")
    # URLエンコード（スペースなど）をデコード
    path = urllib.parse.unquote(path)

    if os.path.exists(path):
        print(f"🚀 起動中: {path}")
        subprocess.Popen(path, shell=True)
    else:
        print(f"⚠️ ファイルが見つかりません: {path}")


if __name__ == "__main__":
    # 引数がある場合は起動処理、ない場合はセットアップを行う
    if len(sys.argv) > 1:
        launch_app(sys.argv[1])
    else:
        register_protocol()
        input("完了しました。エンターキーで閉じます...")