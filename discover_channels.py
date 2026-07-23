import subprocess, json, time

searches = [
    'shorts amazing facts',
    'shorts did you know',
    'shorts interesting facts',
    'shorts mind blowing facts',
    'shorts random facts',
    'shorts daily facts',
    'shorts science facts',
    'shorts nature facts',
    'shorts animal facts',
    'shorts space facts',
    'shorts history facts',
    'shorts psychology facts',
    'shorts food facts',
    'shorts unknown facts',
    'shorts curious facts',
    'shorts fact shorts',
    'shorts knowledge',
    'shorts learn something new',
]

seen = set()
count = 0
for s in searches:
    try:
        r = subprocess.run(
            ['yt-dlp', '--flat-playlist', '--dump-json', '--no-warnings',
             f'ytsearch20:{s}'],
            capture_output=True, text=True, timeout=20
        )
        for line in r.stdout.strip().split('\n'):
            if not line.strip():
                continue
            try:
                d = json.loads(line)
                dur = d.get('duration', 0)
                cid = d.get('channel_id', '')
                if cid in seen or not (10 < dur < 65):
                    continue
                seen.add(cid)
                handle = d.get('uploader_id', '') or d.get('channel', '')[:25]
                ch = d.get('channel', '')[:30]
                title = d.get('title', '')[:40]
                print(f'{count+1:3d}. {handle:30s} | {ch:30s} | {dur:3d}s | {title}')
                count += 1
            except:
                continue
    except:
        continue
    time.sleep(0.5)

print(f'\nTotal unique channels: {count}')
