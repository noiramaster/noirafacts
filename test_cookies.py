import subprocess
import json
import os

# Try yt-dlp with cookies from the running Chrome
result = subprocess.run(
    ['yt-dlp', '--cookies-from-browser', 'chrome', '--flat-playlist', '--dump-json',
     '--no-warnings', 'https://www.instagram.com/natubeac/reels/', '-I', '1:3'],
    capture_output=True, text=True, timeout=30
)
print(f'STDOUT: {result.stdout[:500]}')
print(f'STDERR: {result.stderr[:500]}')

if result.stdout.strip():
    lines = result.stdout.strip().split('\n')
    for line in lines:
        if '{' in line:
            try:
                d = json.loads(line)
                print(f'SUCCESS: {d.get("id")} dur={d.get("duration")}')
            except:
                print(f'JSON line: {line[:100]}')
