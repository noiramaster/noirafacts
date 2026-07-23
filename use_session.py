import requests
import instaloader
import base64
import os
import json

sessionid = "22852400233%3ApBi1X4dH6ir3QK%3A3%3AAYjqJ3092tc-SUxxvA7D9PW1BSiWxNjm-AgCNXdErg"

s = requests.Session()
s.cookies.set('sessionid', sessionid, domain='.instagram.com', path='/')
s.cookies.set('ds_user_id', '22852400233', domain='.instagram.com', path='/')
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
})

L = instaloader.Instaloader(download_pictures=False, download_videos=False, compress_json=False)
L.context._session = s

try:
    profile = instaloader.Profile.from_username(L.context, 'natubeac')
    posts = list(profile.get_posts())[:5]
    print(f'SUCCESS! {len(posts)} posts from @natubeac')
    for p in posts:
        print(f'  - {p.shortcode} video={p.is_video_class} dur={p.video_duration}')
    
    # Save session to file
    L.save_session_to_file()
    session_file = os.path.expanduser('~/.config/instaloader/session-shadow4stories')
    
    if os.path.exists(session_file):
        with open(session_file, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode()
        
        out_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data', 'instagram_session.b64'
        )
        with open(out_path, 'w') as f:
            f.write(encoded)
        print(f'Session saved! ({len(encoded)} chars)')
    else:
        print('Session file not found at expected path')
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
