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

## Run with Docker

Create a `.env` file first:

```env
OPENAI_API_KEY=your_key_here
```

Then run:

```bash
docker compose up -d --build
```

This compose file is set up for a Dockerized Caddy reverse proxy on the shared
`padelkarte_default` network. Caddy should proxy to `jobsearch-app:5000`.

## OpenAI key

- Paste it into the form, or
- Set `OPENAI_API_KEY` in the hosting environment

## Deployment notes

- The Flask app object is exposed in `webapp.py`
- `wsgi.py` is included for WSGI hosting
- Generated files are stored under `APP_GENERATED_DIR` if that environment variable is set
- PDF export still depends on LibreOffice being available on the server or inside the container
- Keep `.env` on the VPS only; do not commit it

## GitHub Deploy Flow

The intended deploy path is:

1. Push changes to GitHub from your local machine
2. Pull the latest code on the VPS
3. Rebuild the hosted app container

Example VPS deploy:

```bash
cd /opt/jobsearch-app
git pull
cd hosted_app
sudo docker compose up -d --build
```

If you change Docker networking or container names, recreate the container:

```bash
cd /opt/jobsearch-app/hosted_app
sudo docker compose down
sudo docker compose up -d --build
```

Current Caddy upstream:

```caddy
cv.padelkarte.com {
  basic_auth {
    rodrigo YOUR_BCRYPT_HASH
  }

  header {
    X-Robots-Tag "noindex, nofollow, noarchive"
  }

  reverse_proxy jobsearch-app:5000
}
```

After changing the Caddyfile on the VPS:

```bash
sudo docker exec -it padelkarte-caddy-1 caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile
```
