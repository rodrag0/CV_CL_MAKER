# Hosted Application Pack Wrapper

This is the web-hosting-ready version of the application pack generator.

## What changed

- Generates files into server-side per-request folders under `generated/`
- Serves downloads back through browser links instead of local filesystem paths
- Produces a ZIP bundle plus individual file downloads
- Cleans up old generated packs automatically

## Run locally

```powershell
cd hosted_app
python -m pip install -r requirements.txt
python webapp.py
```

Open `http://127.0.0.1:5000`.

## OpenAI key

- Paste it into the form, or
- Set `OPENAI_API_KEY` in the hosting environment

## Deployment notes

- The Flask app object is exposed in `webapp.py`
- `wsgi.py` is included for WSGI hosting
- Generated files are stored under `APP_GENERATED_DIR` if that environment variable is set
- PDF export still depends on LibreOffice being available on the server
