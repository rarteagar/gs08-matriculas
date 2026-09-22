# GS08 - Matriculas | Runbook de contenedores (Docker) y Kubernetes

Todos los comandos se ejecutan desde la raiz del repo: `D:\dev\equipo\gs08-matriculas`.
En la maquina de desarrollo el `terminal` de Hermes es bash (git-bash), asi que se usa sintaxis POSIX.

---

## 0. Requisitos (verificado en esta maquina el 21/09/2026)

| Herramienta | Version instalada | Comando de verificacion |
|---|---|---|
| Docker Engine + Compose | Docker 29.8.0 / Compose v5.5.1 | `docker version && docker compose version` |
| kubectl | v1.36.1 | `kubectl version --client` |
| git | 2.54.0 | `git --version` |
| Python (para scripts de validacion) | 3.11.16 | `python --version` |
| Node (solo si se corre el frontend fuera de Docker) | 26.1.0 | `node --version` |

El demonio de Docker Desktop esta corriendo: `docker info` responde `29.8.0 | linux | overlayfs`.
Las imagenes base estan descargadas y fijadas por version: `postgres:16.15-alpine3.24`,
`python:3.12.14-slim-bookworm`, `node:22.23.2-alpine`, `nginx:1.31.6-alpine`,
`prom/prometheus:v3.13.3`, `grafana/grafana:12.4.11`.

---

## 1. Levantar la aplicacion completa (un solo comando)

```bash
cp .env.example .env          # opcional: compose ya trae valores por defecto
docker compose up -d --build  # db + api + api-b + web
docker compose ps             # los 4 contenedores deben decir healthy
```

Servicios y puertos:

| Servicio | Contenedor | URL / puerto en el host | Para que |
|---|---|---|---|
| web (nginx) | gs08-web | http://localhost:8080 | SPA Vue (todo entra por aqui) |
| web (nginx) | gs08-web | http://localhost:8080/api/v1/... | proxy inverso -> API (balanceado) |
| web (nginx) | gs08-web | http://localhost:8080/healthz | healthcheck del contenedor |
| api | gs08-api | http://localhost:8000 | API FastAPI directa (Swagger en /docs) |
| api | gs08-api | http://localhost:8000/metrics | metricas Prometheus |
| api-b | gs08-api-b | (sin puerto al host) | segunda instancia, la usa nginx |
| db | gs08-db | localhost:5432 | PostgreSQL 16 (usuario gs08) |
| prometheus | gs08-prometheus | http://localhost:9090 | solo con `--profile obs` |
| grafana | gs08-grafana | http://localhost:3000 | solo con `--profile obs` |

## 2. Observabilidad (Prometheus + Grafana)

```bash
docker compose --profile obs up -d
# Prometheus: http://localhost:9090/targets   (los 4 targets deben estar UP)
# Grafana:    http://localhost:3000           usuario admin / gs08_grafana
#             dashboard "GS08 - Matriculas y Notas | API RED" ya provisionado
```

El dashboard se provisiona solo desde `infra/grafana/dashboards/gs08-matriculas.json`
(no hay que importarlo a mano). La descripcion de cada panel esta en el propio dashboard
(panel 10) y en `docs/devops/plan-contenedores-ci.md`.

## 3. Ciclo de trabajo diario

```bash
docker compose logs -f api            # logs del API
docker compose logs -f web            # logs de nginx (incluye errores del proxy)
docker compose restart api api-b      # reiniciar sin tocar la base
docker compose exec db psql -U gs08 -d gs08_matriculas   # consola SQL
docker compose exec web cat /etc/nginx/conf.d/default.conf  # ver el nginx.conf generado
docker compose down                   # bajar (conserva datos)
docker compose down -v                # bajar y BORRAR volumenes (pide aprobacion: destruye datos)
```

Reconstruir solo una imagen tras cambiar codigo:

```bash
docker compose build api && docker compose up -d api api-b
docker compose build web && docker compose up -d web
```

## 4. Prueba de balanceo de nginx (2 instancias del API)

```bash
for i in 1 2 3 4; do curl -s -o /dev/null -D - http://localhost:8080/api/v1/estudiantes | grep -i x-upstream-addr; done
```

Debe alternar entre las dos IPs internas (round-robin). Si sale siempre la misma, nginx no
esta viendo ambas instancias: revisar `API_UPSTREAM` en `docker-compose.yml` y que `api-b` este arriba.

## 5. Kubernetes local (k3s o minikube)

```bash
# --- minikube ---
minikube start --cpus 4 --memory 6g
minikube addons enable ingress
eval $(minikube docker-env)            # que las imagenes locales sean visibles al cluster
docker compose build                   # construye gs08-api:local y gs08-web:local
kubectl create namespace gs08
kubectl -n gs08 create secret generic gs08-secrets \
  --from-literal=POSTGRES_PASSWORD='gs08_k8s_pwd' \
  --from-literal=SECRET_KEY="$(openssl rand -hex 32)" \
  --from-literal=DATABASE_URL='postgresql+psycopg://gs08:gs08_k8s_pwd@gs08-db:5432/gs08_matriculas'
kubectl apply -k k8s/
kubectl -n gs08 get pods,svc,ingress

# host local para el Ingress
echo "$(minikube ip)  gs08.local" | sudo tee -a /etc/hosts   # en Windows: editar C:\Windows\System32\drivers\etc\hosts
curl -H "Host: gs08.local" http://$(minikube ip)/healthz
curl -H "Host: gs08.local" http://$(minikube ip)/api/v1/health

# --- k3s --- (usa Traefik: cambiar ingressClassName en k8s/40-ingress.yaml a 'traefik')
kubectl apply -k k8s/
```

Alternativa sin cluster (si no se puede instalar k3s/minikube): desplegar el mismo compose en un
servidor Linux y usar `docker compose up -d`; los manifiestos k8s quedan como entregable de codigo
y se validan con `kubectl apply -k k8s/ --dry-run=client`.

## 6. Integracion continua (GitHub Actions)

```bash
# validacion local de lo mismo que corre el CI:
python scripts/validar_infra.py
docker compose config -q
docker compose build && docker compose up -d && curl -fsS http://localhost:8080/healthz
```

En GitHub: `Actions -> CI` corre en cada pull request (validacion de infra, hadolint, ruff+pytest,
eslint+vitest+build, build de imagenes y smoke test). `CD` publica las imagenes en GHCR despues de
que CI pase en `main`; el despliegue a k8s solo se activa con la variable `DEPLOY_ENABLED=true`.

## 7. Problemas frecuentes

| Sintoma | Causa / solucion |
|---|---|
| `host not found in upstream "api-b"` en los logs de `gs08-web` | nginx no arranca si `api-b` no existe. Levantar el stack completo (`docker compose up -d`), no solo `web`. |
| El API responde 503 en `/health` | PostgreSQL todavia inicializando o credenciales distintas a las del volumen. `docker compose logs db`. |
| Cambio el DDL en `db/init/` y no pasa nada | Los scripts de `docker-entrypoint-initdb.d` corren una sola vez: `docker compose down -v` (borra datos locales). |
| `docker compose config` avisa de variable no definida | Crear `.env` desde `.env.example`. |
| El pull de imagenes llena el disco C: | Docker Desktop guarda las imagenes en el disco del sistema. Mover el disco de datos a `D:` desde Settings > Resources (la unidad C: esta al 94%). |
