import instaloader
import base64
import os

L = instaloader.Instaloader(
    download_pictures=False, download_videos=False, compress_json=False
)

try:
    L.login('shadow4stories', 'aissarah')
    L.save_session_to_file()
    print('LOGIN OK')
    
    session_path = os.path.expanduser('~/.config/instaloader/session-shadow4stories')
    if os.path.exists(session_path):
        with open(session_path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode()
        out_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data', 'instagram_session.b64'
        )
        with open(out_path, 'w') as f:
            f.write(encoded)
        print(f'Session saved ({len(encoded)} chars)')
        
        # Test scraping
        profile = instaloader.Profile.from_username(L.context, 'natubeac')
        posts = list(profile.get_posts())[:3]
        print(f'Test: {len(posts)} posts found')
    else:
        print('Session file not saved')
except instaloader.exceptions.LoginException as e:
    print(f'Login error: {e}')
    if 'checkpoint' in str(e).lower():
        print('Checkpoint required. Opening browser...')
        import subprocess
        subprocess.run(['start', 'https://www.instagram.com/'], shell=True)
except Exception as e:
    print(f'Error: {e}')
