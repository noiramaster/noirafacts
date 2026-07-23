import subprocess
import os
import tempfile
import re


def get_video_info(video_path):
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries',
             'format=duration:stream=width,height',
             '-of', 'json', video_path],
            capture_output=True, text=True, timeout=15
        )
        import json
        info = json.loads(result.stdout)
        streams = info.get('streams', [])
        width = height = 0
        for s in streams:
            if s.get('codec_type') == 'video':
                width = int(s.get('width', 0))
                height = int(s.get('height', 0))
                break
        duration = float(info.get('format', {}).get('duration', 0))
        return width, height, duration
    except:
        return 0, 0, 0


def escape_ffmpeg_text(text):
    text = text.replace("'", "'\\\\''")
    text = text.replace('%', '\\\\%')
    text = text.replace(':', '\\\\:')
    return text


def edit_video(video_path, translated_text, output_path=None):
    w, h, duration = get_video_info(video_path)
    if w == 0 or h == 0:
        return None

    if output_path is None:
        output_path = tempfile.mktemp(suffix='_edited.mp4')

    is_vertical = h > w
    bar_height = int(h * 0.12)
    font_size = max(16, int(bar_height * 0.35))

    needs_resize = False
    target_w, target_h = w, h
    if is_vertical:
        if w < 720:
            scale = 720 / w
            target_w = 720
            target_h = int(h * scale)
            needs_resize = True
    else:
        target_w = 1080
        target_h = 1920
        is_vertical = True
        needs_resize = True

    safe_text = translated_text.replace("'", "\\\\'")

    filter_parts = []

    if needs_resize and not is_vertical:
        filter_parts.append(f'scale={target_w}:{target_h}:force_original_aspect_ratio=decrease')
        filter_parts.append(f'pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:color=black')
    elif needs_resize and is_vertical:
        filter_parts.append(f'scale={target_w}:{target_h}:force_original_aspect_ratio=decrease')
        filter_parts.append(f'pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:color=black')

    drawbox = f'drawbox=x=0:y=0:w=iw:h={bar_height}:color=black@0.6:t=fill'
    filter_parts.append(drawbox)

    wrapped_text = translated_text
    max_chars = max(20, int(w * 0.035))
    if len(translated_text) > max_chars:
        mid = len(translated_text) // 2
        break_point = translated_text.rfind(' ', 0, mid + 10)
        if break_point == -1 or break_point > mid + 15:
            break_point = mid
        line1 = translated_text[:break_point].strip()
        line2 = translated_text[break_point:].strip()
        wrapped_text = line1 + '\\n' + line2
        font_size = int(font_size * 0.9)

    text_y = int(bar_height * 0.15)
    drawtext = (
        f'drawtext=text=\'{safe_text}\':'
        f'x=(w-text_w)/2:y={text_y}:'
        f'fontsize={font_size}:'
        f'fontcolor=white:'
        f'box=1:boxcolor=black@0.4:boxborderw=4:'
        f'font=\'Arial\':'
        f'line_spacing=4'
    )
    filter_parts.append(drawtext)

    filter_complex = ','.join(filter_parts)

    cmd = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-vf', filter_complex,
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-crf', '23',
        '-c:a', 'aac',
        '-b:a', '96k',
        '-movflags', '+faststart',
        output_path
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            return output_path
    except:
        pass

    return None
