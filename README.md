# Noira Pipeline

Sistema automatizado: Instagram → OCR → Traducción → Edición → YouTube Shorts.

## Requisitos

- Python 3.11+
- FFmpeg, Tesseract OCR (con idiomas ara+spa)
- Cuenta Google Cloud con YouTube Data API v3 habilitada
- Cuenta GitHub (para GitHub Actions)
- Cuenta Cloudflare (para dashboard - opcional)

## Setup rápido

### 1. Clonar y configurar

```bash
git clone https://github.com/noiramaster/noirafacts.git
cd noirafacts
cp .env.example .env
pip install -r requirements.txt
```

### 2. YouTube API - Generar Refresh Token

```bash
python src/auth_setup.py --client-id TU_CLIENT_ID --client-secret TU_CLIENT_SECRET
```

Esto abrirá un navegador para autorizar. Copia el refresh token que se imprime.

### 3. Configurar GitHub Secrets

| Secret | Valor |
|---|---|
| `YT_CLIENT_ID` | De Google Cloud |
| `YT_CLIENT_SECRET` | De Google Cloud |
| `YT_REFRESH_TOKEN` | Del paso 2 |

### 4. Subir a GitHub

```bash
git add .
git commit -m "Initial pipeline"
git push origin main
```

El pipeline se ejecutará automáticamente a las 20:00 UTC diarias.

### 5. Dashboard (Cloudflare Pages)

1. Ve a https://dash.cloudflare.com
2. Pages → Conectar con GitHub → selecciona el repo
3. Build command: vacío
4. Output directory: `dashboard`
5. Publicar

## Ejecución manual

```bash
python -m src.main
```

## Límites respetados

- Máximo 6 vídeos/día (YouTube API quota)
- GitHub Actions: ~540 min/mes (de 2000 disponibles)
- Rate limiting entre requests a APIs externas

## Canales Instagram configurados

- @natubeac, @space_aur, @curiosamente, @planetacurioso
- @sabiasque, @datoscuriososoficial, @curiosidad_mental
- @ciencia_curiosa, @mundocurioso, @naturaleza_curiosa
- @sabiasque_ok, @elplanetacurioso

## Arquitectura

```
src/
├── main.py        → Orquestador
├── config.py      → Configuración
├── db.py          → SQLite + esquema
├── scraper.py     → Instagram scraping
├── ocr.py         → Tesseract OCR
├── translator.py  → Traducción
├── editor.py      → FFmpeg edición
├── optimizer.py   → Keywords + metadata
├── uploader.py    → YouTube upload
└── auth_setup.py  → Generar refresh token
```
