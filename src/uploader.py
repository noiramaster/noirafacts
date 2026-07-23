import os
import pickle
import tempfile
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from src.config import YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN


SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
TOKEN_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'yt_token.pickle')


def get_authenticated_service():
    credentials = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as f:
            credentials = pickle.load(f)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
            except:
                credentials = None

        if not credentials:
            if YT_REFRESH_TOKEN:
                from google.oauth2.credentials import Credentials
                credentials = Credentials(
                    token=None,
                    refresh_token=YT_REFRESH_TOKEN,
                    token_uri='https://oauth2.googleapis.com/token',
                    client_id=YT_CLIENT_ID,
                    client_secret=YT_CLIENT_SECRET,
                    scopes=SCOPES
                )
                try:
                    credentials.refresh(Request())
                except:
                    return None
            else:
                return None

        with open(TOKEN_FILE, 'wb') as f:
            pickle.dump(credentials, f)

    return build('youtube', 'v3', credentials=credentials)


def upload_video(video_path, title, description, tags, privacy_status='public'):
    youtube = get_authenticated_service()
    if not youtube:
        return None, 'Authentication failed'

    body = {
        'snippet': {
            'title': title[:100],
            'description': description[:5000],
            'tags': tags[:50],
            'categoryId': '22'
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False,
        }
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

    try:
        request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )
        response = request.execute()
        video_id = response.get('id', '')
        video_url = f'https://youtu.be/{video_id}'
        return video_id, video_url
    except HttpError as e:
        error_content = str(e.content) if hasattr(e, 'content') else str(e)
        if 'quotaExceeded' in error_content or 'quota' in error_content.lower():
            return None, 'quota_exceeded'
        return None, str(e)
    except Exception as e:
        return None, str(e)
