import subprocess, json

cookie = 'C:\\Users\\aissa\\Desktop\\noira-pipeline\\data\\instagram_cookies.txt'

urls = [
    'https://www.instagram.com/natubeac/',
    'https://www.instagram.com/natubeac/?__a=1&__d=1',
]

for url in urls:
    try:
        result = subprocess.run(
            ['yt-dlp', '--cookies', cookie, '--flat-playlist', '--dump-json',
             '--no-warnings', url, '-I', '1:5'],
            capture_output=True, text=True, timeout=30
        )
        lines = [l for l in result.stdout.strip().split('\n') if l.strip() and '{' in l]
        print(f'URL: {url}')
        print(f'  Posts: {len(lines)}')
        if lines:
            for l in lines[:2]:
                d = json.loads(l)
                shortcode = d.get("id", "")
                duration = d.get("duration", 0)
                print(f'  - {shortcode} dur={duration}')
        else:
            err = result.stderr[:200].replace('\n', ' ')
            print(f'  Error: {err}')
    except Exception as e:
        print(f'Exception: {e}')
    print()
