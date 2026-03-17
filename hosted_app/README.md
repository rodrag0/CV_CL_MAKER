# Hosted Application Pack Wrapper

This is the web-hosting-ready version of the application pack generator.

## What changed

- Generates files into server-side per-request folders under `generated/`
- Serves downloads back through browser links instead of local filesystem paths
- Produces a ZIP bundle plus individual file downloads
- Cleans up old generated packs automatically
- Candidate override accepts JSON, raw text, or a PDF resume

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

Current production shape:

- app checkout on the VPS at `/opt/jobsearch-app`
- hosted service in `/opt/jobsearch-app/hosted_app`
- app container name `jobsearch-app`
- Caddy container name `padelkarte-caddy-1`
- Caddy network `padelkarte_default`
- protected app URL `https://cv.padelkarte.com`

## OpenAI key

- Paste it into the form, or
- Set `OPENAI_API_KEY` in the hosting environment

Raw text and PDF profile overrides require OpenAI mode so the app can convert
them into a structured candidate profile before tailoring.

## Deployment notes

- The Flask app object is exposed in `webapp.py`
- `wsgi.py` is included for WSGI hosting
- Generated files are stored under `APP_GENERATED_DIR` if that environment variable is set
- PDF export still depends on LibreOffice being available on the server or inside the container
- Keep `.env` on the VPS only; do not commit it
- The hosted app stores runtime output under `hosted_app/data/`
- The compose file intentionally uses Docker networking instead of host port mapping

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

## Verification

Check that the app container is on the shared Caddy network:

```bash
sudo docker inspect jobsearch-app --format '{{range $k, $v := .NetworkSettings.Networks}}{{println $k}}{{end}}'
```

Expected output:

```text
padelkarte_default
```

Check that Caddy can reach the app by container name:

```bash
sudo docker exec -it padelkarte-caddy-1 sh -lc 'wget -S -O- http://jobsearch-app:5000 2>&1 | head'
```

Check the public endpoint:

```bash
curl -I https://cv.padelkarte.com
```

Expected unauthenticated response:

```text
HTTP/2 401
```

## Troubleshooting

If login works but the browser shows `502`, check the upstream target first.

The correct proxy target is:

```caddy
reverse_proxy jobsearch-app:5000
```

Do not proxy to `127.0.0.1:5000` from Caddy when Caddy is itself running in a
container. Inside the Caddy container, `127.0.0.1` points back to Caddy, not to
the app on the host.
