# Prefect Self-Hosted (Docker)

Setup Prefect 3.x secara self-hosted menggunakan Docker Compose dengan PostgreSQL, Docker Worker, dan Cloudflare Tunnel.

## Arsitektur

```
Internet
   │
   ▼
datahub.kaltarastats.id
   │  (HTTPS via Cloudflare Tunnel)
   ▼
┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ cloudflared │────►│  Prefect Server  │◄────│  Prefect Worker  │
│  (tunnel)   │     │  (API + UI)      │     │  (Docker type)   │
└─────────────┘     └──────┬───────────┘     └──────────────────┘
                           │                         │
                    ┌──────▼───────┐          Docker socket
                    │  PostgreSQL  │          (spawn containers)
                    │  (Database)  │
                    └──────────────┘
```

## Prerequisites

- Docker & Docker Compose
- Akun Cloudflare dengan domain `kaltarastats.id` terdaftar
- Python 3.9+ dan `pip install prefect` (untuk CLI lokal)

## Setup Cloudflare Tunnel

### 1. Buat Tunnel di Cloudflare Dashboard

1. Buka **Cloudflare Zero Trust** → [one.dash.cloudflare.com](https://one.dash.cloudflare.com)
2. Navigasi ke **Networks → Tunnels**
3. Klik **Create a tunnel** → pilih **Cloudflared**
4. Beri nama tunnel, misalnya `datahub`
5. Pada tab **Public Hostname**, tambahkan:
   - **Subdomain**: `datahub`
   - **Domain**: `kaltarastats.id`
   - **Service Type**: `HTTP`
   - **URL**: `prefect-server:4200`
6. Salin **Tunnel Token** yang ditampilkan

### 2. Isi Token di `.env`

```bash
CLOUDFLARE_TUNNEL_TOKEN=isi_token_tunnel_anda_di_sini
```

## Quick Start

### 1. Konfigurasi Environment

Edit `.env`, minimal isi tiga nilai ini:

```bash
POSTGRES_PASSWORD=your_secure_password
CLOUDFLARE_TUNNEL_TOKEN=token_dari_cloudflare_dashboard
```

`PUBLIC_DOMAIN` dan `PREFECT_WORK_POOL_NAME` sudah terisi default yang benar.

### 2. Jalankan Docker Compose

```bash
docker compose up -d
```

Tunggu semua service healthy:

```bash
docker compose ps
```

### 3. Akses Prefect UI

- **Via tunnel (publik)**: https://datahub.kaltarastats.id
- **Via lokal**: http://localhost:4200

## Setup Work Pool

Work pool perlu dibuat agar Worker bisa menerima flow run.

### Cara A: Via UI

1. Buka https://datahub.kaltarastats.id
2. Klik **Work Pools** di sidebar kiri
3. Klik **Create Work Pool**
4. Pilih type: **Docker**
5. Beri nama: `docker-pool` (harus sesuai `PREFECT_WORK_POOL_NAME` di `.env`)
6. Klik **Create**

### Cara B: Via CLI

```bash
export PREFECT_API_URL=https://datahub.kaltarastats.id/api

prefect work-pool create docker-pool --type docker
prefect work-pool ls
```

## Deploy Flow Pertama

### 1. Install Prefect client

```bash
pip install prefect
```

### 2. Arahkan client ke server publik

```bash
export PREFECT_API_URL=https://datahub.kaltarastats.id/api
```

### 3. Test flow secara lokal (opsional)

```bash
python flows/hello_world.py
```

### 4. Deploy flow ke server

Buat file `flows/deploy.py`:

```python
from hello_world import hello_world

if __name__ == "__main__":
    hello_world.deploy(
        name="hello-world-deployment",
        work_pool_name="docker-pool",
        image="prefecthq/prefect:3-latest",
        job_variables={"image_pull_policy": "Always"},
        push=False,
    )
```

Jalankan deploy:

```bash
cd flows
python deploy.py
```

### 5. Trigger flow run

Via CLI:

```bash
prefect deployment run hello-world/hello-world-deployment
```

Atau klik **Run** di Prefect UI pada halaman deployment.

### 6. Monitor

- UI: https://datahub.kaltarastats.id
- Log worker: `docker compose logs -f prefect-worker`
- Log tunnel: `docker compose logs -f cloudflared`

## Perintah Berguna

```bash
# Lihat semua logs
docker compose logs -f

# Restart semua service
docker compose restart

# Stop semua service (data tetap ada di volume)
docker compose down

# Stop dan hapus semua data (reset penuh)
docker compose down -v

# Lihat status worker
prefect worker ls
```

## Struktur File

```
datahub/
├── docker-compose.yml   # Service definitions (postgres, server, worker, cloudflared)
├── .env                 # Environment variables (credentials, domain, tunnel token)
├── README.md            # Dokumentasi ini
└── flows/
    └── hello_world.py   # Contoh flow sederhana
```

## Troubleshooting

**UI tidak bisa load data (API error di browser):**
- Pastikan `PREFECT_UI_API_URL` di `docker-compose.yml` sesuai domain Anda
- Ini terjadi jika browser mencoba memanggil API ke `localhost` alih-alih domain publik

**Tunnel tidak konek:**
- Pastikan `CLOUDFLARE_TUNNEL_TOKEN` di `.env` sudah diisi dengan token yang benar
- Cek log: `docker compose logs cloudflared`
- Pastikan public hostname di Cloudflare dashboard mengarah ke `prefect-server:4200`

**Worker tidak konek ke server:**
- Pastikan work pool sudah dibuat dengan nama yang sesuai di `.env`
- Cek logs: `docker compose logs prefect-worker`

**Flow run stuck di "Scheduled":**
- Pastikan Worker sudah running dan terhubung ke pool yang benar
- Pastikan Docker socket ter-mount: cek volume `/var/run/docker.sock`

**Database connection error / password authentication failed:**
- Jika volume sudah ada dari instalasi sebelumnya, jalankan `docker compose down -v` lalu `docker compose up -d`
- Cek credential di `.env` konsisten
