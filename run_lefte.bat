@echo off
:: 作業フォルダへ移動
cd /d "C:\Users\iwaya\Documents\htt"

:: 既に動いているPythonを掃除してリセット
taskkill /f /im python.exe /t >nul 2>&1

:: システムが落ち着くまで少し待機
timeout /t 3 /nobreak >nul

:: 1. カレンダーサーバー (Port 5000) を単独で起動
echo Starting Calendar Server (5000)...
:: 構成を維持したまま、Pythonの出力だけを error_log.txt へ保存するように変更
start "Lefte_Python" /b cmd /c "python lefte_server.py > error_log.txt 2>&1"

:: 2秒待ってから次を起動（これが重要です）
timeout /t 2 /nobreak >nul

:: 2. 画面表示サーバー (Port 8000) を単独で起動
echo Starting HTTP Server (8000)...
start "Lefte_HTML" /b python -m http.server 8000

:: 最後に動作ログを残す（トラブル時に確認用）
echo Started at %date% %time% > startup_log.txt