"""
Genera Refresh Token de YouTube.
Abre navegador para autorizar. Sigue las instrucciones.
"""

import argparse
import webbrowser
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
CLIENT_CONFIG = {
    'installed': {
        'client_id': '',
        'client_secret': '',
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
    }
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--client-id', required=True)
    parser.add_argument('--client-secret', required=True)
    args = parser.parse_args()

    CLIENT_CONFIG['installed']['client_id'] = args.client_id
    CLIENT_CONFIG['installed']['client_secret'] = args.client_secret

    print('Abriendo navegador para autorizar YouTube API...')
    flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
    credentials = flow.run_local_server(
        port=8080,
        open_browser=True,
        authorization_prompt_message=''
    )

    print('\n' + '=' * 60)
    print('REFRESH TOKEN (copia esto para GitHub Secrets):')
    print('=' * 60)
    print(credentials.refresh_token)
    print('=' * 60)


if __name__ == '__main__':
    main()
