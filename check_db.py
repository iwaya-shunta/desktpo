import sqlite3

# データベースに接続
conn = sqlite3.connect('chat_history.db')
c = conn.cursor()

# データを全件表示
c.execute("SELECT timestamp, role, content FROM messages")
rows = c.fetchall()

print(f"--- 履歴データ全 {len(rows)} 件 ---")
for row in rows:
    print(f"[{row[0]}] {row[1]}: {row[2][:30]}...") # 長い場合は省略して表示

conn.close()