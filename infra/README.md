# Infra: Deployment & Containers

Direktori ini berisi konfigurasi deployment dan infrastruktur:
- `docker-compose.yml`: Lingkungan orkestrasi pengujian lokal (web frontend, agent worker, mock services).
- Dockerfile untuk agent worker Python.
- Skrip konfigurasi deployment container (Railway / Fly.io / VPS cadangan).
- Skrip cadangan self-hosting LiveKit Server jika kuota cloud habis.
