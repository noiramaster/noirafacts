import pytesseract
from PIL import Image, ImageFilter, ImageEnhance
import subprocess
import os
import json
import tempfile
import re


def extract_frame(video_path, timestamp='00:00:01', output_path=None):
    if output_path is None:
        output_path = tempfile.mktemp(suffix='.png')
    subprocess.run(
        ['ffmpeg', '-y', '-ss', timestamp, '-i', video_path,
         '-vframes', '1', '-q:v', '2', output_path],
        capture_output=True, text=True, timeout=30
    )
    return output_path if os.path.exists(output_path) else None


def crop_top_bar(image_path, bar_height_ratio=0.12):
    img = Image.open(image_path)
    w, h = img.size
    bar_height = int(h * bar_height_ratio)
    cropped = img.crop((0, 0, w, bar_height))
    cropped_path = tempfile.mktemp(suffix='_bar.png')
    cropped.save(cropped_path)
    return cropped_path


def preprocess_image(image_path):
    img = Image.open(image_path)
    w, h = img.size

    img = img.resize((w * 3, h * 3), Image.LANCZOS)

    if img.mode != 'L':
        img = img.convert('L')

    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)

    img = img.filter(ImageFilter.SHARPEN)
    img = img.filter(ImageFilter.SHARPEN)

    _, threshold_path = tempfile.mkstemp(suffix='_thresh.png')
    img.save(threshold_path)
    return threshold_path


def detect_arabic_percentage(text):
    arabic_range = range(0x0600, 0x06FF + 1)
    arabic_chars = sum(1 for c in text if ord(c) in arabic_range)
    total_chars = len(text.strip())
    if total_chars == 0:
        return 0
    return arabic_chars / total_chars


def ocr_image(image_path, lang='ara+eng'):
    try:
        img = Image.open(image_path)
        custom_config = '--oem 3 --psm 7 -c tessedit_char_whitelist='
        text = pytesseract.image_to_string(img, lang=lang)
        confidence_data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)
        confidences = [c for c in confidence_data['conf'] if c > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        text = text.strip()
        return text, avg_confidence
    except Exception as e:
        return '', 0


def detect_source_language(text):
    if not text.strip():
        return 'unknown'
    arabic_pct = detect_arabic_percentage(text)
    if arabic_pct > 0.3:
        return 'ar'
    return 'auto'


def ocr_video(video_path):
    frame_path = extract_frame(video_path)
    if not frame_path:
        return '', 0, 'unknown'

    bar_path = crop_top_bar(frame_path)
    processed_path = preprocess_image(bar_path)

    text, confidence = ocr_image(processed_path)

    for p in [frame_path, bar_path, processed_path]:
        try:
            os.remove(p)
        except:
            pass

    lang = detect_source_language(text)
    return text, confidence, lang
