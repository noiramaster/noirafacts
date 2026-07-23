"""Save Instagram cookies for yt-dlp and test scraping"""

import os
import json
import subprocess

sessionid = "22852400233%3ApBi1X4dH6ir3QK%3A3%3AAYjqJ3092tc-SUxxvA7D9PW1BSiWxNjm-AgCNXdErg"
ds_user_id = "22852400233"
csrftoken = "zqjPmHyCUHlqyRNBeR24kDgeBv1j4c3f"

# Create Netscape-format cookie file for yt-dlp
cookie_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'instagram_cookies.txt')
os.makedirs(os.path.dirname(cookie_file), exist_ok=True)

with open(cookie_file, 'w') as f:
    f.write("# Netscape HTTP Cookie File\n")
    f.write("# https://curl.haxx.se/rfc/cookie_spec.html\n")
    f.write(".instagram.com\tTRUE\t/\tTRUE\t\tcsrftoken\t" + csrftoken + "\n")
    f.write(".instagram.com\tTRUE\t/\tTRUE\t\tsessionid\t" + sessionid + "\n")
    f.write(".instagram.com\tTRUE\t/\tTRUE\t\tds_user_id\t" + ds_user_id + "\n")

print(f'Cookie file saved: {cookie_file}')

# Test yt-dlp with cookies
result = subprocess.run(
    ['yt-dlp', '--cookies', cookie_file, '--flat-playlist', '--dump-json',
     '--no-warnings', 'https://www.instagram.com/natubeac/reels/', '-I', '1:5'],
    capture_output=True, text=True, timeout=30
)

if result.stdout.strip():
    lines = result.stdout.strip().split('\n')
    valid = [l for l in lines if l.strip() and '{' in l]
    print(f'\nFound {len(valid)} posts:')
    for v in valid:
        d = json.loads(v)
        print(f'  - {d.get("id")} dur={d.get("duration")}')
else:
    print(f'\nNo output. Stderr: {result.stderr[:300]}')
    
    # Try alternative URL format
    print('\nTrying alternative URL format...')
    result2 = subprocess.run(
        ['yt-dlp', '--cookies', cookie_file, '--flat-playlist', '--dump-json',
         '--no-warnings', 'https://www.instagram.com/api/v1/users/web_profile_info/?username=natubeac',
         '-I', '1:5'],
        capture_output=True, text=True, timeout=15
    )
    print(f'Stdout: {result2.stdout[:300]}')
    print(f'Stderr: {result2.stderr[:300]}')
