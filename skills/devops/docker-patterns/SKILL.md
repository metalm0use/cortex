---
schema_version: 1
tags:
  - "devops"
  - "docker"
  - "containers"
  - "security"
topics:
  - "docker compose"
  - "containerized development"
  - "dockerfile hardening"
status: seed
created: 2026-06-07
updated: 2026-07-03
sources:
  - "https://github.com/affaan-m/ECC/blob/main/skills/docker-patterns/SKILL.md"
  - "project owner Docker Compose preferences, captured 2026-06-07"
source_count: 2
aliases:
  - "docker"
  - "docker compose"
  - "container patterns"
  - "dockerfile security"
skill_id: devops/docker-patterns
summary: "Apply Docker and Docker Compose patterns for local development, service wiring, volumes, and container hardening."
model_role: reference
depends_on: []
related:
  - sql/injection
  - meta/contributing
review_status: human-noted
reviewed_by:
  - "project owner"
expertise_domain:
  - "docker compose"
  - "container operations"
confidence: low
reviewed_at: 2026-06-07
---

# Docker Patterns

<!-- learned: 2026-06 | project: cortex-skill-import | model: thinking-model -->

Use this skill when creating, reviewing, or troubleshooting Dockerfiles,
Compose files, local containerized development stacks, service networking,
volumes, or basic container hardening.

## Core Rule

Keep development containers ergonomic, production images minimal and
reproducible, and service boundaries explicit. Do not trade away
repeatability or security for a shorter Dockerfile.

## Workflow

1. Identify the target mode: local development, test, production image,
   or production orchestration. Use Compose freely for local development;
   do not assume a plain Compose stack is enough for production scheduling,
   rolling deploys, secrets, and recovery.
2. Use `compose.yaml` for the primary Compose file. Use explicit
   secondary files such as `compose.prod.yaml` only when the mode needs a
   distinct override.
3. Add `env_file` to every service that reads runtime configuration.
   When key variables should be visible in Compose, pass them explicitly
   through `environment` with `${VAR}` expansion backed by `.env`.
4. Split Dockerfiles into stages when build tooling differs from runtime
   needs. Keep dependency installation, development, build, and production
   runtime concerns separate.
5. Wire Compose services by service name on the internal network. Expose
   host ports only when a human or host process must connect.
6. Choose volume types deliberately: bind mounts for editable source,
   first-party named volumes for persistent service data, and anonymous
   volumes to protect container-generated dependency folders from host
   bind mounts.
7. Harden images before shipping: pin base image tags, run as a non-root
   user, avoid baking secrets into layers, drop capabilities where
   practical, and add a health check that exercises the real service.
8. Verify with `docker compose config`, a clean rebuild, service logs,
   and an end-to-end request through the same port or network path users
   will use.

## Compose Patterns

For a local web stack, use named services and health-aware dependencies:

```yaml
# compose.yaml
services:
  app:
    build:
      context: .
      target: dev
    env_file:
      - .env
    ports:
      - "${APP_PORT:-3000}:3000"
    volumes:
      - .:/app
      - /app/node_modules
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      NODE_ENV: ${NODE_ENV:-development}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    command: npm run dev

  db:
    image: postgres:16-alpine
    env_file:
      - .env
    ports:
      - "127.0.0.1:${POSTGRES_PORT:-5432}:5432"
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    env_file:
      - .env
    volumes:
      - redisdata:/data

volumes:
  pgdata:
  redisdata:
```

Back it with a checked-in example and a gitignored local file:

```dotenv
# .env.example
APP_PORT=3000
DATABASE_URL=postgres://postgres:postgres@db:5432/app_dev
REDIS_URL=redis://redis:6379/0
NODE_ENV=development
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=app_dev
```

### Layered env files for orchestrator-injected secrets

When a deploy tool (Komodo, Portainer, a CI runner) writes a secrets file
onto the host at deploy time, split configuration by sensitivity instead of
gitignoring everything. Commit a non-secret `.env`, and load a gitignored
secret overlay with `required: false` so the stack still runs locally
without it. Compose merges env files in order, so the overlay overrides the
committed base — use it for both secrets and host-specific values.

```yaml
services:
  app:
    env_file:
      - path: .env # committed: non-secret config, loaded first
        required: true
      - path: .env.komodo # gitignored: secrets + host overrides, injected at deploy
        required: false
```

Only `.env` is auto-loaded for `${VAR}` interpolation in the Compose file
itself, so values that live solely in the overlay must be consumed via
`env_file` injection into the container, not via `${VAR}` substitution.
Gitignore the overlay; commit a `*.example` template documenting its keys.

Keep development overrides separate from production overrides:

```yaml
# compose.override.yaml, auto-loaded by docker compose
services:
  app:
    env_file:
      - .env
    environment:
      DEBUG: ${DEBUG:-app:*}
      LOG_LEVEL: ${LOG_LEVEL:-debug}
    ports:
      - "${NODE_INSPECT_PORT:-9229}:9229"
```

```yaml
# compose.prod.yaml, loaded explicitly
services:
  app:
    build:
      target: production
    restart: always
```

Run production-like Compose commands explicitly so the active file set is
visible:

```bash
docker compose -f compose.yaml -f compose.prod.yaml up -d
```

## Reverse Proxy & Tunnel Exposure

When fronting a service with a reverse proxy or an outbound tunnel
(Cloudflare Tunnel, Tailscale Funnel, Traefik, nginx):

- Put the proxy/tunnel and the app on a shared user-defined network and have
  the proxy reach the app by **container name** over that network. Do not
  publish the app's port to the host just to connect the proxy to it; if a
  host publish is required, bind it to `127.0.0.1`.
- Terminate TLS at the edge/proxy and let the app speak plain **HTTP** on its
  internal port. Point the proxy at `http://<service>:<port>`.
- Keep admin/setup UIs (and any management port) off the public path entirely
  — LAN/loopback only.
- Mind the request-body limit of the path. CDNs and tunnels cap upload size
  per request (e.g. Cloudflare's 100 MB on Free/Pro). Prefer apps that do
  **chunked uploads** under that cap rather than assuming unlimited bodies;
  downloads are usually uncapped.
- HTTP tunnels carry HTTP(S) only. Services needing **UDP or arbitrary TCP**
  (TURN/VoIP, game servers, WireGuard) will not work through them — expose
  those separately.

### Traefik label-based routing (owner standard)

<!-- learned: 2026-07 | project: remote-access-gateway | model: thinking-model -->

When a Compose service should be reachable through the Traefik ingress,
declare the route with labels on the service — do not publish host ports.
Use this label block as the default shape whenever creating such a service:

```yaml
services:
  myapp:
    labels:

      # Traefik - General Configuration
      traefik.enable: true
      traefik.http.services.myapp.loadbalancer.server.port: 3000

      # Traefik - Routers
      traefik.http.routers.myapp-secure.service: myapp
      traefik.http.routers.myapp-secure.entrypoints: https
      traefik.http.routers.myapp-secure.rule: Host(`myapp.$DOMAIN`)
      traefik.http.routers.myapp-secure.tls: true
      traefik.http.routers.myapp-secure.tls.certresolver: default
```

Conventions:

- One named Traefik **service** per container, with
  `loadbalancer.server.port` set to the app's internal HTTP port (Traefik
  cannot infer it reliably when the container exposes several).
- Router named `<name>-secure`, bound to the `https` entrypoint with
  `tls: true` and `tls.certresolver: default` — no plain-HTTP router;
  the proxy handles redirect.
- Host rule uses `$DOMAIN` from the env file rather than a hardcoded
  domain, keeping the Compose file portable across environments.
- `traefik.enable: true` is required per service (the proxy runs with
  `exposedByDefault: false`).
- Traefik discovers labels via the Docker provider, so it must share a
  user-defined network with the container and run on the same host.

## Volume Strategy

Prefer first-party named volumes for service-owned persistent data. This
keeps ownership visible in Compose, avoids anonymous host directories,
and makes backup, migration, and destructive cleanup decisions explicit.

When data must live on a compliant host drive, keep the Compose surface a
named volume and use driver options for the host path:

```yaml
volumes:
  pgdata:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${DATA_ROOT}/postgres
```

Use direct bind mounts for source code, local fixtures, or files the
developer intentionally edits from the host. Do not use direct bind
mounts as the default shape for database, cache, queue, object storage,
or other first-party service state.

## Dockerfile Patterns

Use multi-stage builds to keep runtime images smaller and cleaner:

```dockerfile
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS dev
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build && npm prune --production

FROM node:22-alpine AS production
WORKDIR /app
RUN addgroup -g 1001 -S appgroup && adduser -S appuser -u 1001
USER appuser
COPY --from=build --chown=appuser:appgroup /app/dist ./dist
COPY --from=build --chown=appuser:appgroup /app/node_modules ./node_modules
COPY --from=build --chown=appuser:appgroup /app/package.json ./package.json
ENV NODE_ENV=production
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost:3000/health || exit 1
CMD ["node", "dist/server.js"]
```

Add a `.dockerignore` early. At minimum, exclude dependency folders,
VCS data, local environment files, build output, logs, coverage, and
test-only artifacts that should not enter the build context.

## Security Checks

- Pin base image versions instead of using `latest`.
- Run production processes as a non-root user.
- Put secrets in runtime configuration, a secret manager, or Docker
  secrets where applicable; never set real secrets with `ENV` in the
  Dockerfile.
- In Compose, add `security_opt: ["no-new-privileges:true"]`,
  `cap_drop: ["ALL"]`, and `read_only: true` when the application can
  tolerate them. Add `tmpfs` mounts for writable scratch paths.
- Avoid publishing database, cache, and internal API ports in production.
  Internal service discovery by Compose service name usually removes the
  need for host exposure.
- Keep secrets out of committed files. The simplest form is to gitignore
  `.env` and commit `.env.example`; where a deploy tool injects a secrets
  overlay, a non-secret `.env` may be committed as long as secrets live only
  in the gitignored overlay (see "Layered env files"). Either way, surface
  values through `env_file` rather than hardcoding them in Compose.

## Troubleshooting

Start with the smallest observation that proves where the failure lives:

```bash
docker compose config
docker compose ps
docker compose logs -f app
docker compose exec app sh
docker compose exec app nslookup db
docker compose exec app wget -qO- http://db:5432
docker compose build --no-cache app
```

Treat cleanup commands according to their blast radius. `docker compose
down` removes containers and default networks for the project; `docker
compose down -v` also removes named volumes and can destroy local
database state.

## Anti-Patterns

- One large container that runs unrelated services.
- Data stored only inside a container filesystem.
- First-party service data kept in direct host bind mounts when a named
  volume would preserve ownership and cleanup semantics.
- Root production containers without a specific reason.
- Unpinned base images in reproducible builds.
- Committed secrets — in `.env`, an env overlay, or Compose files. (A
  committed `.env` is fine only when it holds no secrets.)
- Host-published ports for services that only other containers need.

## Completion Criteria

The Docker or Compose change is ready when the active configuration is
inspectable, a clean build succeeds, services can resolve each other by
name, the primary Compose file is `compose.yaml`, each configured service
uses `env_file` with explicit variable pass-through where useful,
persistent first-party data uses named volumes, secrets are not baked
into images or committed config, and the runtime image follows the
least-privilege checks that the application can support.

## Human Review Notes

<!-- learned: 2026-06 | project: cortex-docker-preferences | model: human-mediated -->

- 2026-06-07 | status: human-noted | confidence: low | kind: preference | reviewer: project owner | domain: docker compose, container operations
  Prefer the current Compose file name `compose.yaml`, include `env_file`
  even when variables are also listed explicitly under `environment`, and
  prefer first-party named volumes for persistent service data. Named
  volumes may use local-driver bind options when data must live on a
  specific compliant host drive. This is captured as owner preference and
  operational style, not as independent certification of Docker behavior.
