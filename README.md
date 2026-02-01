# L.E.F.T.E. AI Assistant v5.5.1 Master
デスクトップとモバイルの垣根を越える、次世代のパーソナル AI アシスタント。

## ✨ 特徴
- **Soul Integration**: タイプライター演出、音声同期ビジュアライザーによる「生命感」のある対話。
- **Stable UI**: ニュース、カレンダー、チャットを統合した 3 パネル・レスポンシブデザイン。
- **Secure Remote Access**: Tailscale を利用した安全な外出先からのアクセスに対応。
- **Multi-Model**: Gemini 3 Flash / Pro を用途に合わせて瞬時に切り替え可能。

## 🌐 API & Network Configuration
- **Gemini API**: 思考エンジン（1.5 Flash / Pro 推奨）
- **VOICEVOX API**: 音声合成（Speaker ID: 8 推奨）
- **Tailscale**: MagicDNS と SSL 証明書（tailscale cert）によるセキュアな HTTPS 通信。
- **Public APIs**: Open-Meteo (天気), RSS2JSON (ニュース)

## 🚀 セットアップ
1. `pip install -r requirements.txt` を実行。
2. `.env.example` をコピーして `.env` を作成し、API キーを入力。
3. `python lefte_server.py` で起動！