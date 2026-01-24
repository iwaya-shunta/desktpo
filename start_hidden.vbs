Set ws = CreateObject("WScript.Shell")
ws.Run "cmd /c C:\Users\iwaya\Documents\htt\run_lefte.bat", 0, False
ws.run "cmd /c C:\Program Files\VOICEVOX\vv-engine\run.exe", 0
Set ws = Nothing