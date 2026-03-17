# Hosted App Deploy

This deployment flow matches the current VPS setup:

- app repo checkout at `/opt/jobsearch-app`
- hosted service under `/opt/jobsearch-app/hosted_app`
- Dockerized Caddy in the separate `padelkarte` stack
- shared Docker network `padelkarte_default`
- Caddy upstream `jobsearch-app:5000`
- public app URL `https://cv.padelkarte.com`
- Basic Auth enabled in Caddy

## First-time VPS setup

Clone the repository to the VPS:

```bash
cd /opt
git clone <your-repo-url> jobsearch-app
cd /opt/jobsearch-app/hosted_app
cp .env.example .env
```

Edit `.env` and set the real OpenAI key.

Start the app:

```bash
sudo docker compose up -d --build
```

Make sure the Caddyfile in `/opt/padelkarte/Caddyfile` proxies to:

```caddy
reverse_proxy jobsearch-app:5000
```

Then reload Caddy:

```bash
sudo docker exec -it padelkarte-caddy-1 caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile
```

## Normal deploy

Push from local:

```bash
git add .
git commit -m "Describe the change"
git push
```

Pull and rebuild on the VPS:

```bash
cd /opt/jobsearch-app
git pull
cd hosted_app
sudo docker compose up -d --build
```

## When to use `down` first

Run a full recreate if you changed:

- `docker-compose.yml`
- container networking
- container name
- mounted volumes

```bash
cd /opt/jobsearch-app/hosted_app
sudo docker compose down
sudo docker compose up -d --build
```

## Verification

Check the app container:

```bash
cd /opt/jobsearch-app/hosted_app
sudo docker compose ps
```

Check that Caddy can reach the app:

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

After authenticating in the browser, the app should render normally. If the
browser shows `502`, the most likely cause is that Caddy is still proxying to
`127.0.0.1:5000` instead of `jobsearch-app:5000`.
