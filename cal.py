import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle
import datetime

# スコープの設定
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_google_credentials():
    creds = None
    
    TOKEN_FILE = 'token.pickle'
    
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=8888)  # ← 空いてるポートを指定
        
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds


def get_calendar_service():
    try:
        creds = get_google_credentials()
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        st.error(f"認証エラーが発生しました: {e}")
        return None



def main():
    st.title('Google Calendarアプリ')
    
    service = get_calendar_service()
    if service:
        st.success('Google Calendarに接続しました！')

        # 予定の取得
        st.header('予定の取得')
        if st.button('今日の予定を取得'):
            now = datetime.datetime.utcnow().isoformat() + 'Z' # UTC時間で指定
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])

            if not events:
                st.info('今日の予定はありません。')
            else:
                st.subheader('今後の10件の予定:')
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    st.write(f"- {start}: {event['summary']}")

        # 予定の登録
        st.header('予定の登録')
        with st.form(key='event_form'):
            summary = st.text_input('予定のタイトル')
            start_date = st.date_input('開始日')
            end_date = st.date_input('終了日')
            
            submit_button = st.form_submit_button(label='予定を登録')
        
        if submit_button:
            event = {
                'summary': summary,
                'start': {
                    'date': str(start_date),
                },
                'end': {
                    'date': str(end_date),
                },
            }
            
            try:
                event = service.events().insert(calendarId='primary', body=event).execute()
                st.success(f"予定が登録されました: {event.get('htmlLink')}")
            except Exception as e:
                st.error(f"予定の登録に失敗しました: {e}")

if __name__ == '__main__':
    main()
