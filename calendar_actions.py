import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os

# 認証情報の取得（lefte_server.pyから分離して再利用できるようにします）
def get_calendar_service():
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/calendar'])
        return build('calendar', 'v3', credentials=creds)
    return None

def list_calendar_events(max_results=10):
    """直近の予定を確認します。"""
    service = get_calendar_service()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=max_results, singleEvents=True,
                                        orderBy='startTime').execute()
    return events_result.get('items', [])

def add_calendar_event(summary, start_time, end_time, description=""):
    """新しい予定を追加します。引数の日時は ISO 8601 形式（例: 2026-01-25T10:00:00+09:00）です。"""
    service = get_calendar_service()
    event = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': start_time, 'timeZone': 'Asia/Tokyo'},
        'end': {'dateTime': end_time, 'timeZone': 'Asia/Tokyo'},
    }
    return service.events().insert(calendarId='primary', body=event).execute()

def delete_calendar_event(event_id):
    """指定されたIDの予定を削除します。"""
    service = get_calendar_service()
    service.events().delete(calendarId='primary', eventId=event_id).execute()
    return f"Event {event_id} deleted."

def update_calendar_event(event_id, summary=None, start_time=None, end_time=None):
    """既存の予定を変更します。"""
    service = get_calendar_service()
    event = service.events().get(calendarId='primary', eventId=event_id).execute()
    if summary: event['summary'] = summary
    if start_time: event['start']['dateTime'] = start_time
    if end_time: event['end']['dateTime'] = end_time
    return service.events().update(calendarId='primary', eventId=event_id, body=event).execute()