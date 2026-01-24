import io
import os.path
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials


# 認証情報の取得（カレンダーと共通の token.json を使います）
def get_drive_service():
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        return build('drive', 'v3', credentials=creds)
    return None


def list_drive_files(page_size: int = 10):
    """Google ドライブ内のファイル名とIDのリストを取得します。"""
    service = get_drive_service()
    results = service.files().list(
        pageSize=page_size, fields="nextPageToken, files(id, name, mimeType)").execute()
    items = results.get('files', [])

    if not items:
        return "ファイルは見つからなかったよ。"

    output = "ドライブ内のファイルリストだよ：\n"
    for item in items:
        output += f"- {item['name']} (ID: {item['id']}, 種類: {item['mimeType']})\n"
    return output


def read_drive_file_content(file_id: str):
    """指定されたIDのファイル（テキストまたはGoogleドキュメント）の内容を読み取ります。"""
    service = get_drive_service()

    # ファイルの情報を取得して、Googleドキュメントか普通のファイルか判別する
    file_metadata = service.files().get(fileId=file_id).execute()
    mime_type = file_metadata.get('mimeType')

    if mime_type == 'application/vnd.google-apps.document':
        # Google ドキュメントの場合はテキストとしてエクスポート
        request = service.files().export_media(fileId=file_id, mimeType='text/plain')
    else:
        # 普通のテキストファイルなどの場合はそのままダウンロード
        request = service.files().get_media(fileId=file_id)

    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()

    return fh.getvalue().decode('utf-8')