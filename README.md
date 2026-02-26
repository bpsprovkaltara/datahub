# Prefect Self-Hosted (Docker)

Setup Prefect 3.x secara self-hosted menggunakan Docker Compose dengan PostgreSQL dan Docker Worker.

## Arsitektur

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  PostgreSQL   │◄────│  Prefect Server  │◄────│  Prefect Worker  │
│  (Database)   │     │  (API + UI)      │     │  (Docker type)   │
└──────────────┘     └──────────────────┘     └──────────────────┘
                            │                         │
                       port 4200                Docker socket
                       (UI & API)               (spawn containers)
```

## Prerequisites

- Docker & Docker Compose
- Python 3.9+ (untuk deploy flow dari local)
- `pip install prefect` (client CLI)

## Quick Start

### 1. Konfigurasi Environment

Edit file `.env` sesuai kebutuhan. Minimal ganti password:

```bash
POSTGRES_PASSWORD=your_secure_password
```

### 2. Jalankan Docker Compose

```bash
docker compose up -d
```

Tunggu semua service healthy:

```bash
docker compose ps
```

### 3. Akses Prefect UI

Buka browser: **http://localhost:4200**

## Setup Work Pool

Work pool perlu dibuat agar Worker bisa menerima flow run. Ada dua cara:

### Cara A: Via UI

1. Buka http://localhost:4200
2. Klik **Work Pools** di sidebar
3. Klik **Create Work Pool**
4. Pilih type: **Docker**
5. Beri nama: `docker-pool` (harus sesuai dengan `PREFECT_WORK_POOL_NAME` di `.env`)
6. Klik **Create**

### Cara B: Via CLI

Set API URL ke server Anda, lalu buat pool:

```bash
export PREFECT_API_URL=http://localhost:4200/api

prefect work-pool create docker-pool --type docker
```

Verifikasi pool aktif:

```bash
prefect work-pool ls
```

## Deploy Flow Pertama

### 1. Install Prefect client

```bash
pip install prefect
```

### 2. Arahkan client ke server

```bash
export PREFECT_API_URL=http://localhost:4200/api
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

- Lihat status flow run di UI: http://localhost:4200
- Lihat log worker: `docker compose logs -f prefect-worker`

## Perintah Berguna

```bash
# Lihat semua logs
docker compose logs -f

# Restart semua service
docker compose restart

# Stop semua service (data tetap ada di volume)
docker compose down

# Stop dan hapus semua data
docker compose down -v

# Lihat status worker
prefect worker ls
```

## Struktur File

```
datahub/
├── docker-compose.yml   # Service definitions
├── .env                 # Environment variables
├── README.md            # Dokumentasi ini
└── flows/
    └── hello_world.py   # Contoh flow sederhana
```

## Troubleshooting

**Worker tidak konek ke server:**
- Pastikan work pool sudah dibuat dengan nama yang sesuai di `.env`
- Cek logs: `docker compose logs prefect-worker`

**Flow run stuck di "Scheduled":**
- Pastikan Worker sudah running dan terhubung ke pool yang benar
- Pastikan Docker socket ter-mount: cek volume `/var/run/docker.sock`

**Database connection error:**
- Tunggu PostgreSQL selesai startup (healthcheck)
- Cek credential di `.env` konsisten
