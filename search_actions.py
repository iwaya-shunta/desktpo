# ここを duckduckgo_search から ddgs に書き換えてね！
from ddgs import DDGS


def search_web(query: str):
    """最新の情報をウェブで検索します。"""
    print(f"🔍 最新の情報を調査中...: {query}")
    try:
        # 使い方は今までと同じで大丈夫だよ！
        with DDGS() as ddgs:
            # 2026年現在の仕様に合わせてリスト内包表記で取得
            results = [r for r in ddgs.text(query, max_results=5)]

            if not results:
                return "ごめん、有力な情報が見つからなかったみたい。"

            formatted_results = []
            for r in results:
                formatted_results.append(f"【{r['title']}】\n{r['body']}\n(URL: {r['href']})")

            return "\n---\n".join(formatted_results)
    except Exception as e:
        return f"検索中にトラブルが起きちゃった：{str(e)}"