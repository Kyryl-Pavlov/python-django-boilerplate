# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Security Measures

The following security controls are intentionally in place. Do not remove or weaken them without a documented reason.

### Application

| Measure | Location | Rule |
|---|---|---|
| `SECRET_KEY` fail-fast | `app/settings/base.py` — `_require()` | Raises `RuntimeError` at startup if unset. Never add a default fallback value. |
| Upload size limit | `nginx/nginx.conf` — `client_max_body_size 50m` | Applied on both `/api/` and `/graphql` locations. Django itself has no built-in size cap; Nginx is the enforcement point. |
| File upload allowlist | `app/api/v1/views/media.py` — `_ALLOWED_EXTENSIONS` | Allowlist of safe extensions only. Extend deliberately; never switch to a blocklist. |
| SQL masking in logs | `app/logging/data_filter.py` — `sanitize_traceback()` | Strips `[SQL: ...]`, `[parameters: ...]`, and connection strings from every traceback before it reaches any log backend. Lambda has an inline equivalent `_safe_exc()` in `lambda/handler.py`. |
| GraphQL introspection | `app/settings/development.py` + `app/settings/production.py` | `GRAPHQL_INTROSPECTION = True` in development only; `False` in production. Do not hardcode `True`. |
| Explicit JWT algorithm | `app/settings/base.py` — `SIMPLE_JWT["ALGORITHM"] = "HS256"` | Pinned to prevent silent algorithm changes on library upgrades. |

### Infrastructure (Terraform)

| Measure | Location | Rule |
|---|---|---|
| Redis TLS | `terraform/modules/elasticache/main.tf` | `transit_encryption_enabled = true`. Output URL is `rediss://` (double-s). Both must stay in sync. |
| Non-root containers | `Dockerfile`, `lambda/Dockerfile`, `lambda/Dockerfile.lambda` | App uses a `app` system user; Lambda uses `nobody`. The `USER` instruction must remain after all `COPY`/`RUN` steps. |
| ECS task role SQS scope | `terraform/modules/iam/main.tf` | Django app: `sqs:SendMessage` + `sqs:GetQueueAttributes` only. Lambda worker: `ReceiveMessage` + `DeleteMessage`. Never cross-assign. |
| Secrets Manager recovery | `terraform/main.tf`, `terraform/modules/rds/main.tf` | `recovery_window_in_days = 7`. Never set to `0` in committed code (risk of unrecoverable accidental deletion). |
| WAF logging | `terraform/modules/waf/main.tf` | CloudWatch log group `aws-waf-logs-{prefix}`, 90-day retention. Do not remove `aws_wafv2_web_acl_logging_configuration`. |

### Nginx

| Measure | Location | Rule |
|---|---|---|
| Security headers | `nginx/nginx.conf` | `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, `server_tokens off`. All use `always` flag so they apply to error responses too. |
| HSTS | `nginx/nginx.conf` (commented) | Enable `Strict-Transport-Security` **only after** TLS is live on the ALB. Enabling it over HTTP permanently breaks access for returning visitors. |

### Intentional gaps (not implemented by design)

- **Content-Security-Policy** — commented in `nginx/nginx.conf`. A CSP covering the GraphQL playground requires per-deployment origin config; a wrong CSP silently breaks the playground. Add once you know your frontend origins.
- **HSTS** — see above.
- **Redis AUTH token** — cluster is in a private subnet accessible only via security group. Add `auth_token` when moving to multi-tenant or shared infrastructure.
- **MIME type sniffing** — files go to S3 and are never executed server-side; extension allowlisting is sufficient. Add `python-magic` if serving files from a public CDN without `Content-Disposition: attachment`.
- **JWT refresh token blacklisting** — stateless by design. Add a Redis-backed blacklist if logout must immediately invalidate tokens.

## Common Commands

```bash
# Start full stack (rebuilds image)
docker compose up --build

# Rebuild and start only the app container
docker compose up --build app

# Run DB migrations inside container
docker compose run --rm migrate python manage.py migrate

# Migrations run automatically on every docker compose up --build.
# The migrate service applies all pending migrations on startup.
# To run manually (e.g. outside Docker):
python manage.py makemigrations app -m "description"
python manage.py migrate

# Tail app logs
docker compose logs -f app
```

### Helper Scripts

**`migrate.sh`** — interactive migration helper for local development (runs outside Docker, requires Django installed in the active virtual environment). Prompts for a migration message, runs `makemigrations`, then asks whether to immediately apply with `migrate`.

```bash
bash migrate.sh
```

**`start_infra.sh`** — starts only the infrastructure services (Postgres, LocalStack, migrations) in detached mode. Used when running the Django app on the host for local debugging.

```bash
bash start_infra.sh
# To stop: docker compose stop postgres localstack
```

**`launch_app_docker_image.sh`** — builds the production Docker image standalone (no compose, no infrastructure) and starts a single detached container on port 5000. Useful for smoke-testing the image in isolation. After startup it hits `/api/v1/health` to verify the server is up and prints the GraphQL playground URL.

```bash
bash launch_app_docker_image.sh
# To stop: docker stop django-boilerplate
```

> Note: this script starts only the app container with no database or LocalStack, so any endpoint that touches Postgres or S3 will fail. Use it only to verify the image builds and the process starts cleanly.

## Debugging

Two VSCode debug configurations are defined in `.vscode/launch.json`:

### Option 1 — Attach to running Docker container

The `app` service in `docker-compose.yml` uses `Dockerfile.dev`, which starts Django under `debugpy` on port 5678. The debugger is always available while the stack is running.

```bash
docker compose up --build
```

Then launch **"Docker: Attach to Django"** in VSCode. Source changes are picked up immediately via the volume mount (no rebuild needed).

### Option 2 — Run Django on the host

Start only infrastructure, then launch **"Local: Django Debug"** in VSCode (F5). The `preLaunchTask` runs `docker compose up -d postgres localstack migrate` automatically; `postDebugTask` stops them when the session ends.

The launch config overrides `DATABASE_URL` and S3 endpoint vars to use `localhost` instead of Docker service hostnames. If your `.env.local` uses different Postgres credentials, update `DATABASE_URL` in `.vscode/launch.json` accordingly.

## Local Infrastructure

The full stack runs via Docker Compose. All services share the default Docker network.

| Service | Port | Purpose |
|---|---|---|
| `nginx` | 80 | Reverse proxy / load balancer — single entry point for all services |
| `app` | 5000, 5678 | Django app (uvicorn + debugpy on 5678) — also reachable directly on 5000 |
| `postgres` | 5432 | Primary database |
| `migrate` | — | One-shot container: runs `python manage.py migrate` on startup |
| `localstack` | 4566 | AWS S3 + CloudWatch Logs emulator |
| `pgadmin` | 5050 | Postgres GUI |
| `s3-console` | 8080 | S3 bucket GUI (cloudlena/s3manager) |
| `loki` | 3100 | Log aggregation — receives structured JSON from `LokiLogger` |
| `prometheus` | 9090 | Metrics database — scrapes `/metrics` from `app` every 15 s |
| `grafana` | 3000 | Dashboards — queries Prometheus (metrics) and Loki (logs) |
| `cadvisor` | 8081 | Container resource metrics (CPU, mem, disk) — **non-functional on Docker Desktop for Windows**, included for production parity only |
| `node-exporter` | 9100 | Host OS metrics (CPU, memory, disk I/O, network, load average) via `/proc` and `/sys` |

**Startup order:** `postgres` healthy → `localstack` healthy → `migrate` completes → `app` starts → `nginx` starts.

**Adding a new microservice behind Nginx:**
1. Add the service to `docker-compose.yml` (no ports needed — it stays internal).
2. Add an upstream block and a `location` block to `nginx/nginx.conf`.
3. Restart: `docker compose up --build nginx`.

Other services reach the Django app internally via `http://app:5000` (direct) or `http://nginx/api/v1/` (through the proxy). External clients always hit port 80.

**S3 bucket init:** `localstack-init/create-bucket.sh` runs via LocalStack's `/etc/localstack/init/ready.d` hook, creating the `media-bucket`. The service also auto-creates the bucket on first upload via `_ensure_bucket()`.

**Environment:** All config lives in `.env.local`, loaded via `env_file` in compose. Never committed — use `.env.local` as the single source of truth for local development.

## Architecture

### Django App Structure

`app/` is a single Django app. Settings are split by environment in `app/settings/` (base, development, production, testing). The active environment is selected via `DJANGO_SETTINGS_MODULE`.

`app/apps.py` — `AppAppConfig.ready()` initializes `AppLogger` and `CacheService` once at startup and stores them on the AppConfig instance. Access from views: `apps.get_app_config('app').logger_adapter`.

### Dual API Layer

Every feature is exposed over both REST and GraphQL. Both share the same models and services — only the transport layer differs.

- **REST:** `app/api/v1/` — DRF `APIView` classes mounted at `/api/v1/`
- **GraphQL:** `app/graphql_api/` — graphene-django schema at `/graphql`, with `graphene-file-upload` for multipart uploads

GraphQL resolvers extract the JWT manually from `info.context["request"].META.get("HTTP_AUTHORIZATION")` using `get_token_from_bearer()` / `verify_access_token()` from `app/graphql_api/utils.py`, since graphene doesn't use DRF's authentication pipeline.

### Configuration

`app/settings/base.py` contains all env vars read via `os.getenv()`. `SECRET_KEY` is fail-fast via `_require()`. All AWS/S3 settings must be in `base.py`, not only in `development.py`, or they will be absent in production mode.

### S3 / LocalStack Split Endpoint

The S3 service (`app/services/aws_s3_service.py`) maintains two boto3 client modes:

- `_client()` — uses `AWS_S3_ENDPOINT_URL` (`http://localstack:4566`) for internal operations (upload). Resolvable only inside Docker.
- `_client(public=True)` — uses `AWS_S3_PUBLIC_ENDPOINT_URL` (`http://localhost:4566`) for generating presigned URLs. Needed because presigned URLs are opened by the browser on the host machine, which cannot resolve the `localstack` hostname.

In production both env vars are unset (`None`), so boto3 routes to real AWS automatically.

### Models

All models live in `app/models/` and are registered via `app/models/__init__.py`. Django discovers them automatically via `INSTALLED_APPS = ['app']`. Current models:

- `User` — UUID PK, `email` (unique), `AbstractBaseUser` with `BCryptSHA256PasswordHasher`; `AUTH_USER_MODEL = 'app.User'`
- `Media` — UUID PK, `user` (FK → User ON DELETE CASCADE), `content_key` (S3 object key, **not** a URL), `created_at`
- `Event` — UUID PK, `sqs_message_id` (unique, indexed), `type`, `payload` (JSON), `status`, timestamps

`content_key` stores the S3 key (`media/<user_uuid>/<filename>`). Presigned URLs are generated on demand and never persisted.

### Logging

The app uses an Object Adapter pattern. All loggers implement `LoggerProtocol` (`app/utils/logger.py`) and are injected into `AppLogger`, which fans out calls to all of them.

| Class | Location | Behaviour |
|---|---|---|
| `AppLogger` | `app/logging/logger.py` | Fanout adapter; single public method `log(message, level, data, exc)`. `Level` enum exposed as `AppLogger.Level.{INFO,WARN,ERROR}` |
| `ConsoleLogger` | `app/logging/logger.py` | stdout via Python `logging`; DEBUG in dev, WARNING in prod |
| `SentryLogger` | `app/logging/sentry_logger.py` | `info`/`warn` → Sentry breadcrumbs; `error` → `capture_message` with extras |
| `CloudWatchLogger` | `app/logging/cloudwatch_logger.py` | Structured JSON events via `watchtower`; supports `endpoint_url` for LocalStack |
| `LokiLogger` | `app/logging/loki_logger.py` | POSTs structured JSON to Loki's `/loki/api/v1/push`; uses stdlib `urllib` only (no extra dependency); failures are silently swallowed |

`AppLogger` is initialized in `AppAppConfig.ready()` (`app/apps.py`) and stored as `AppAppConfig.logger_adapter`. Sentry, CloudWatch, and Loki are **opt-in** — only wired when their env vars are set. CloudWatch init failure is non-fatal. Loki push failures are silently swallowed.

**Loki labels:** every event is tagged with `{app: "django-boilerplate", env: <settings_env>, level: <info|warning|error>}`. Query in Grafana Explore with `{app="django-boilerplate"}` or `{level="error"}`.

**Request logging:** `RequestLoggingMiddleware` (`app/middleware/logging.py`) logs method, path, status, duration_ms for every request via AppLogger at INFO level.

**Manual logging:**
```python
# In a route handler (has access to Request):
logger = request.app.state.logger_adapter
logger.log("upload failed", level=logger.Level.ERROR, data={"key": s3_key}, exc=e)

# In a GraphQL resolver (has access to context):
logger = info.context.logger_adapter
logger.log("upload failed", level=logger.Level.ERROR, data={"key": s3_key}, exc=e)
```

**Data filtering:** `mask_sensitive()` in `app/logging/data_filter.py` recursively replaces values of sensitive keys (`password`, `token`, `secret`, `authorization`, etc.) with `***`. Applied automatically in `AppLogger.log()` before any logger sees the data. To add keys, extend `_SENSITIVE_KEYS` in `data_filter.py`.

**Sentry notes:**
- JWT auth failures return 401 from `app/security.py` — Sentry captures these via `DjangoIntegration` automatically.
- `info`/`warn` calls appear as breadcrumbs inside Sentry error events, not as standalone events. This is intentional — sending every log as an event burns Sentry quota.

**CloudWatch / LocalStack notes:**
- LocalStack must have `logs` in `SERVICES` (already set in `docker-compose.yml`).
- On Windows with Git Bash, prefix every `aws logs` CLI command with `MSYS_NO_PATHCONV=1` to prevent Git Bash from converting `/myapp/dev` → `C:/Program Files/Git/myapp/dev`.
- Query logs locally: `MSYS_NO_PATHCONV=1 aws --endpoint-url=http://localhost:4566 logs get-log-events --log-group-name /myapp/dev --log-stream-name app`

### Observability Stack

The app ships a **collect → store → visualise** pipeline:

```
Django /metrics   ──scrape──►  Prometheus  ──PromQL──►  Grafana
AppLogger         ──push───►   Loki        ──LogQL───►  Grafana
node-exporter     ──scrape──►  Prometheus
cAdvisor          ──scrape──►  Prometheus  (non-functional on Docker Desktop)
```

**Grafana provisioning (auto-wired on startup):**
- `grafana/provisioning/datasources/datasources.yml` — registers Prometheus (uid: `prometheus`) and Loki (uid: `loki`) automatically. No manual UI setup needed.
- `grafana/provisioning/dashboards/dashboards.yml` — loads all JSON files from `grafana/dashboards/` on startup.
- `grafana/dashboards/django-app.json` — App dashboard: request rate, error rate, p95/p99 latency stats, request rate by status/handler, latency by handler, error logs, all logs. Metrics use `django-prometheus` names (`django_http_requests_total_by_view_transport_method`, `django_http_responses_total_by_status`).
- `grafana/dashboards/host-metrics.json` — Host Metrics dashboard: CPU usage (total/user/system/iowait), memory (used/buffers/cached/free), network I/O, disk I/O, load average (1m/5m/15m), open file descriptors.
- Default credentials: `admin` / `admin` (set via `GF_SECURITY_ADMIN_PASSWORD` in `docker-compose.yml`).

**Prometheus metrics (`django-prometheus`):**
- Wired via `django_prometheus.middleware.PrometheusBeforeMiddleware` / `PrometheusAfterMiddleware` in `MIDDLEWARE` and `path('', include('django_prometheus.urls'))` in `urls.py`.
- Exposes `/metrics` in Prometheus text format.
- Key metrics: `django_http_requests_total_by_view_transport_method`, `django_http_responses_total_by_status`, DB query counts.
- `prometheus.yml` scrapes `app:5000/metrics`, `cadvisor:8080/metrics`, and `node-exporter:9100/metrics` every 15 s.

**Node Exporter (host OS metrics):**
- Mounts `/proc`, `/sys`, and `/` read-only from the host and exposes kernel-level metrics: `node_cpu_seconds_total`, `node_memory_MemAvailable_bytes`, `node_filesystem_avail_bytes`, `node_disk_read_bytes_total`, `node_network_receive_bytes_total`, `node_load1/5/15`.
- Works correctly on Docker Desktop for Windows because it reads from `/proc` and `/sys`, which Docker Desktop maps properly into the WSL2 VM (unlike cAdvisor which needs the overlayfs layer database).
- **Scope:** entire host (or WSL2 VM on Windows) — not per-container. Use cAdvisor for per-container breakdowns.

**cAdvisor (container resource metrics):**
- `gcr.io/cadvisor/cadvisor:v0.47.2` — pinned because v0.55+ requires the containerd socket at `/run/containerd/containerd.sock`, which Docker Desktop for Windows does not expose at that path. v0.47.2 uses the Docker HTTP API but still cannot read `/var/lib/docker/image/overlayfs/layerdb/mounts/` on Docker Desktop (path mismatch in the WSL2 VM). Effectively non-functional on Windows Docker Desktop — included for production parity. On a real Linux host it works without changes.
- **Scope:** per-container CPU, memory, network, disk — complements Node Exporter which only shows host totals.

**Node Exporter vs cAdvisor:**
- Node Exporter answers "how loaded is the host?" — total CPU %, memory pressure, disk space, network throughput.
- cAdvisor answers "which container is responsible?" — per-container breakdown of the same resources.
- Both are needed for full visibility; Node Exporter works locally, cAdvisor does not on Docker Desktop.

**Production on AWS Fargate — neither tool runs:**
Fargate is serverless — there is no accessible host OS, Docker socket, or cgroup filesystem. Replace the entire local observability stack with AWS-managed equivalents:

| Local | AWS Fargate |
|---|---|
| Node Exporter + cAdvisor | **CloudWatch Container Insights** — enabled with one ECS cluster setting; collects per-task CPU, memory, network natively from the Fargate hypervisor |
| Prometheus scraping `/metrics` | **ADOT sidecar** (AWS Distro for OpenTelemetry) — runs as a second container in the same Fargate task, scrapes `localhost:5000/metrics`, ships to Amazon Managed Prometheus (AMP) |
| Prometheus (storage) | **Amazon Managed Prometheus (AMP)** |
| Loki | **CloudWatch Logs** — already wired via `CloudWatchLogger`; no changes needed |
| Grafana | **Amazon Managed Grafana (AMG)** — connects to AMP and CloudWatch as data sources |

The only app-side requirement for the production setup is the `/metrics` endpoint — ADOT picks it up without any code changes.

**Adding a new logger backend:**
1. Create a class in `app/logging/` implementing `LoggerProtocol` (`info`, `warning`, `error` methods).
2. Instantiate it conditionally in `AppAppConfig.ready()` (`app/apps.py`) and append to `loggers`.
3. Add the required env var to `app/settings/base.py`.

### Error Handling

Each REST view and GraphQL resolver wraps risky operations (DB queries, S3 calls, UUID parsing) in individual `try/except` blocks with specific messages and appropriate status codes. Django's ORM auto-rolls back the transaction on unhandled exceptions.

DRF authentication/permission errors are caught by `custom_exception_handler` in `app/api/exceptions.py`, which wraps them in the standard `{success, message, data, status_code}` envelope.

**S3 `_ensure_bucket`:** `head_bucket` raises `ClientError(404)`, not `client.exceptions.NoSuchBucket`. Always catch `botocore.exceptions.ClientError` and check `e.response["Error"]["Code"]` — catching the named exception variant silently falls through and skips bucket creation.

## Separation of Concerns

Each layer has a strict responsibility. Do not cross these boundaries:

| Layer | Location | Responsibility |
|---|---|---|
| **Models** | `app/models/` | Django ORM model definitions only — no business logic, no imports from API or service layers |
| **Services** | `app/services/` | External integrations (S3, SQS, future: email, payments). Read config directly from `os.getenv()` — no framework context assumptions |
| **REST views** | `app/api/v1/views/` | Parse request, validate input via serializers, call services/models, return `api_response()`. No raw dict returns |
| **REST serializers** | `app/api/v1/serializers/` | DRF serializers for input validation. Pure serialization only — no service calls |
| **REST utils** | `app/api/utils.py` | `api_response()` helper. All reusable REST helper functions live here |
| **GraphQL queries/mutations** | `app/graphql_api/queries/`, `app/graphql_api/mutations/` | Mirror REST views. Return per-resolver response types. No direct HTTP response logic |
| **GraphQL utils** | `app/graphql_api/utils.py` | Token extraction helpers (`get_token_from_bearer`, `verify_access_token`, `verify_refresh_token`) |
| **GraphQL types** | `app/graphql_api/types.py` | Graphene ObjectType definitions only — no resolver logic |
| **Settings** | `app/settings/` | All configuration via `os.getenv()`. Env vars are never read directly in views or services |
| **Logging** | `app/logging/` | `AppLogger` + logger adapters, `mask_sensitive` data filter. Logger stored on `AppAppConfig.logger_adapter`; accessed via `apps.get_app_config('app').logger_adapter` |

## Code Quality

Pre-commit hooks enforce formatting and linting on every `git commit`. Install once after setting up the dev virtualenv:

```bash
pip install -r requirements-dev.txt
pre-commit install
```

| Hook | Files | Behaviour |
|---|---|---|
| `trailing-whitespace` | non-`.py` | Removes trailing spaces |
| `end-of-file-fixer` | non-`.py` | Ensures files end with a newline |
| `check-yaml` | `.yml`/`.yaml` | Validates YAML syntax |
| `check-toml` | `.toml` | Validates TOML syntax |
| `check-merge-conflict` | all | Fails on unresolved `<<<<<<<` markers |
| `debug-statements` | `.py` | Fails on `breakpoint()` / `pdb.set_trace()` |
| `ruff` (autofix + format) | `.py` | Runs `ruff format` + `ruff check --fix`, re-stages fixed files, then checks for unfixable issues |

**Commit behaviour:**
- Autofixable issues → fixes are applied and staged into the commit automatically (single commit, no second pass needed)
- Unfixable issues → commit aborts with the specific error printed

Run all hooks on the entire codebase without committing:

```bash
pre-commit run --all-files
```

Tool config lives in `pyproject.toml` (`[tool.ruff]`). The hook script is `scripts/ruff_hook.py`.

## Testing

### Structure

Tests live under `tests/app/` mirroring the source tree:

```
tests/
└── app/
    ├── unit/          — pure functions, zero external deps (run in < 1 s)
    │   ├── api/         api_response() envelope, response format
    │   ├── graphql_api/ token extraction helpers
    │   ├── logging/     mask_sensitive(), AppLogger fanout, CloudWatch serialization
    │   └── services/    CacheService JSON wrap/unwrap, TTL, ping
    ├── integration/   — DRF APIClient + SQLite in-memory via pytest-django (no Docker needed)
    └── e2e/           — real HTTP against the full CI stack (Docker required)
```

### Running tests

```bash
# Install test dependencies (includes pytest, pytest-django, pytest-cov, requests)
pip install -r requirements-test.txt

# Unit + integration — no Docker needed, < 1 s
pytest tests/app/unit tests/app/integration

# With coverage report
pytest tests/app/unit tests/app/integration --cov=app --cov-report=term-missing

# E2E — requires the CI stack to be running
docker compose -f docker-compose.ci.yml up -d --wait
pytest tests/app/e2e
docker compose -f docker-compose.ci.yml down
```

`pytest.ini` at the project root sets `DJANGO_SETTINGS_MODULE = app.settings.testing`. `testing.py` seeds `SECRET_KEY` via `os.environ.setdefault` before `base.py` is loaded, so no env var is required to run tests.

### Coverage

Current baseline: **128 tests, < 1 s**. Intentional gaps:
- `aws_s3_service`, `aws_sqs_service` — SDK wiring only, no project logic to verify
- `loki_logger`, `sentry_logger` — thin SDK call wrappers

### Key fixtures (`tests/app/integration/conftest.py`)

| Fixture | What it does |
|---|---|
| `client` | DRF `APIClient` for REST requests |
| `registered_user` | Creates a user via `POST /api/v1/auth/register`, returns credentials dict |
| `access_token` | Logs in `registered_user`, returns access token string |
| `refresh_token` | Logs in `registered_user`, returns refresh token string |
| `auth_headers` | `{"HTTP_AUTHORIZATION": "Bearer <access_token>"}` — pass as `**auth_headers` to `client.post(...)` |
| `mock_cache` | Replaces `AppAppConfig.cache` with a `MagicMock`; restores `None` after the test |
| `gql` | Posts a GraphQL query to `/graphql`, returns the response |
| `gql_auth_headers` | Like `auth_headers` but via the GraphQL login mutation, returns `{"access": {...}, "refresh": {...}}` |

All integration tests must be marked `@pytest.mark.django_db`. The `db` fixture (from pytest-django) provides a fresh SQLite in-memory database for each test.

### Gotchas

**GraphQL vs REST auth** — resolvers call `get_token_from_bearer()` + `verify_access_token()` from `app/graphql_api/utils.py` manually. GraphQL always returns HTTP 200 — success/failure lives in `response.data.<resolver>.success`. Integration tests pass `Authorization` headers as Django META keys (`HTTP_AUTHORIZATION`).

**DRF kwargs for auth** — in test calls, pass auth as `**auth_headers` (which unpacks to `HTTP_AUTHORIZATION="..."`) not as a `headers=` dict, since `APIClient` uses Django's META naming convention.

**Password hasher in tests** — `testing.py` uses `MD5PasswordHasher` (fast) instead of BCrypt. This is test-only; production always uses BCrypt.

**E2E `BASE_URL`** — defaults to `http://localhost/api/v1`. Override via `E2E_BASE_URL` env var to point at staging or any other environment.

### Adding tests for a new feature

1. Unit tests in `tests/app/unit/<layer>/` for any new pure/utility functions.
2. REST integration tests in `tests/app/integration/test_<resource>.py` — mark class/functions with `@pytest.mark.django_db`.
3. GraphQL integration tests in `tests/app/integration/test_graphql_<resource>.py`.
4. Add the happy-path to `tests/app/e2e/test_e2e.py` if it involves a new infrastructure dependency (new AWS service, new DB table, etc.).
5. Mock at the service-function boundary: `patch("app.api.v1.views.<module>.<fn>")` or `patch("app.graphql_api.mutations.<module>.<fn>")`.

## Style Guide

**Naming:**
- Do not use leading underscores for function or variable names (`process_record`, not `_process_record`). Python's underscore-private convention is not used in this codebase.
- S3 object paths are called `content_key` (never `content_url`) — they are keys, not URLs. Presigned URLs are transient and never stored.
- GraphQL type fields use snake_case in Python; Graphene auto-converts to camelCase in the schema (`media_id` → `mediaId`). The Postman collection uses camelCase field names for GraphQL responses.
- REST response fields use snake_case throughout (`access_token`, `refresh_token`, `media_id`).

**Responses:**
- REST: always use `api_response(success, message, data, status_code)` from `app/api/utils.py`. Returns a DRF `Response` — never return a raw dict.
- GraphQL: always return a per-resolver response type (e.g. `AuthResponse`, `StringResponse`) with `success`, `message`, and optionally `data`. Never raise exceptions from resolvers.

**Authentication:**
- REST views: set `authentication_classes = [JWTAuthentication]` and `permission_classes = [IsAuthenticated]`.
- GraphQL resolvers: call `get_token_from_bearer(auth_header)` + `verify_access_token(token)` / `verify_refresh_token(token)` inside a `try/except` at the top of the resolver — graphene resolvers do not use DRF's authentication pipeline.

**Postman collection:** `postman_collection.json` at the repo root must be kept in sync with API changes. Update it whenever you add, remove, or rename an endpoint or change a request/response shape. The collection has two top-level folders — **REST** and **GraphQL** — each covering all endpoints (auth, media, events, cache, health). Collection-level variables (`base_url`, `access_token`, `refresh_token`, `media_id`) are shared across both folders. Test scripts on the Login and Upload File requests in both folders auto-capture tokens and IDs so subsequent requests chain without manual copy-paste.

**Adding a new feature:**
1. Add/update the Django model in `app/models/` and register it in `app/models/__init__.py`.
2. Generate and apply a migration: `python manage.py makemigrations app -m "description" && python manage.py migrate`.
3. Add any external service logic to `app/services/`.
4. Add a DRF `APIView` in `app/api/v1/views/`, a serializer in `app/api/v1/serializers/`, and wire the URL in `app/api/v1/urls.py`.
5. Add graphene Query/Mutation classes in `app/graphql_api/queries/` and `app/graphql_api/mutations/`, then include them in `Query` and `Mutation` in `app/graphql_api/schema.py`.
6. Add the corresponding Graphene type to `app/graphql_api/types.py` if needed.

## Lambda Worker Dockerfiles

`lambda/handler.py` supports two runtimes from the same file:
- `handler(event, context)` — Lambda entry point, called by AWS when SQS delivers a batch
- `poll()` — long-running SQS polling loop, called via `if __name__ == "__main__"` for local dev

Two Dockerfiles exist for these two runtimes:

| File | Used by | CMD |
|---|---|---|
| `lambda/Dockerfile` | `docker-compose.yml` worker service | `python handler.py` → runs `poll()` |
| `lambda/Dockerfile.lambda` | `deploy.yml` CI/CD worker image build | `handler.handler` → Lambda RIC calls `handler()` |

Never use `Dockerfile` for the CI/CD image build — it produces a long-running process that is not a valid Lambda container. The deploy workflow already references `Dockerfile.lambda`.

## CI/CD Pipeline

### Workflows

**`.github/workflows/ci.yml`** — triggers on every push and pull request.

Three parallel jobs:
- `lint` — `ruff format --check` + `ruff check`
- `test` — `pytest tests/app/unit tests/app/integration` with SQLite in-memory (no Docker)
- `e2e` — spins up `docker-compose.ci.yml`, runs `pytest tests/app/e2e`, tears down with `-v`

**`.github/workflows/deploy-dev.yml`** — targets the `dev` environment; triggers manually by default (change to `push: branches: [develop]` to enable automatic deploys on merge).

**`.github/workflows/deploy-prod.yml`** — targets the `production` environment; manual trigger only. Approval gate is on the `migrate` job — approving it unlocks `deploy` and `deploy-workers` for the same run.

The two files are intentionally separate — no branch conditionals, each file has one purpose. They are structurally identical; the only differences are the branch image tag (`develop` vs `main`) and the `environment:` value.

### Job structure

```
build  (all images in parallel)
  ├── migrate-dev          (develop branch — runs ALL migrations before any deploy)
  │     ├── deploy-dev         (needs: [build, migrate-dev] — services in tier order)
  │     └── deploy-workers-dev (needs: [build, migrate-dev] — Lambda workers, parallel with services)
  └── migrate-prod         (main branch — approval gate; approving unlocks entire prod pipeline)
        ├── deploy-prod
        └── deploy-workers-prod
```

### Deploy order within each environment

Migrations are a separate job that must complete before any service or worker is touched:

1. **`migrate-*`** — runs ALL service migrations as one-off ECS Fargate tasks. If any migration fails the entire pipeline stops. Schema is always ahead of code.
2. **`deploy-*`** (services) and **`deploy-workers-*`** (Lambda) — start in parallel once migrate completes. Services deploy in tier order within the job (tier-1 first, then dependents); workers are independent.

### Backward-compatible migrations rule

During a rolling ECS update, old and new task instances run simultaneously against the same database. Every migration must be backward-compatible with the currently-deployed code:
- **Safe**: add a nullable column, add an index, add a table
- **Unsafe**: drop a column the old code still reads, rename a column, change a type non-compatibly

Use a two-phase approach for breaking changes: first deploy adds the new column (old code ignores it), second deploy removes the old column once all instances run the new code.

### Adding a new microservice

1. Add its ECR repo to `terraform/modules/ecr/main.tf`
2. Add its ECS service + task definition to `terraform/` (or a new module)
3. Add a build step to the `build` job in `deploy.yml`
4. Add a `run_migration` call in `migrate-dev` and `migrate-prod` (if it has its own DB)
5. Add a deploy step in `deploy-dev` and `deploy-prod` at the correct tier
6. Add its GitHub environment vars (`*_TASK_FAMILY`, `*_SERVICE`) via `terraform output`

### Required GitHub secrets and variables

**Repository secret** (Settings → Secrets → Actions):
- `AWS_ROLE_ARN` — IAM role for OIDC authentication, output by `terraform output github_actions_role_arn`

**Per-environment variables** (Settings → Environments → `dev` / `production`):
- `ECS_CLUSTER`, `ECS_SERVICE`, `APP_TASK_FAMILY` — from `terraform output`
- `VPC_SUBNETS`, `VPC_SECURITY_GROUPS` — from `terraform output` (used for migration task networking)
- `LAMBDA_FUNCTION_NAME` — from `terraform output`

### CI stack (`.env.ci`)

The CI stack uses `.env.ci` (committed, contains only fake test credentials). It sets `APP_ENV=production` to test the production code path. LocalStack provides S3 and SQS. No real AWS credentials are needed for CI.

## Terraform Infrastructure

All AWS infrastructure is declared in `terraform/`. Terraform is an infra-owner operation — run manually when provisioning or changing infrastructure. The CI/CD pipeline handles all ongoing app deployments.

### Module structure

```
terraform/
├── bootstrap/        # Run once: S3 state bucket + DynamoDB lock table (local state)
├── environments/
│   ├── dev.tfvars    # Small sizes, no HTTPS, relaxed WAF, no deletion protection
│   └── prod.tfvars   # Multi-AZ RDS, deletion protection, HTTPS required, 2 ECS tasks
├── modules/
│   ├── networking    # VPC, public/private subnets, NAT gateway, 5 security groups, VPC flow logs
│   ├── ecr           # ECR repos for app + worker; scan on push; keep last 10 images
│   ├── iam           # ECS task execution role, ECS task role, Lambda role, GitHub OIDC role
│   ├── rds           # PostgreSQL 16 encrypted; DATABASE_URL secret in Secrets Manager
│   ├── elasticache   # Redis 7 replication group; encrypted at rest
│   ├── s3            # Media bucket; public access blocked; HTTPS-only bucket policy
│   ├── sqs           # events queue + DLQ; SSE; redrive after 3 failures
│   ├── alb           # ALB; HTTP→HTTPS redirect; TLS 1.3; drop invalid headers
│   ├── waf           # OWASP Top 10, bad inputs, SQLi, per-IP rate limit
│   ├── ecs           # Fargate cluster; task def with secrets from Secrets Manager; service
│   └── lambda        # Container image function in VPC; SQS event source mapping
├── main.tf           # Wires all modules; creates JWT + Django app secrets in Secrets Manager
├── variables.tf      # All inputs (sizes, flags, image URIs, GitHub org/repo, state bucket)
├── outputs.tf        # All values needed for GitHub environment vars, labelled
└── versions.tf       # AWS ~> 5.0, random ~> 3.0; partial S3 backend
```

### State management

State is stored in S3 with DynamoDB locking. The S3 bucket and DynamoDB table are created by `terraform/bootstrap/` with local state (the bootstrap is the only exception to "never use local state").

`backend.hcl` — fill-in file referencing the state bucket and lock table. **Gitignored** — never committed.

### Bootstrap and first deploy

```bash
# 1. Create state infrastructure (once per AWS account)
cd terraform/bootstrap
terraform init
terraform apply -var="bucket_name=myorg-django-boilerplate-tfstate"
# Copy outputs → fill in backend.hcl and environments/*.tfvars

# 2. Init main module
cd ../
terraform init -backend-config=backend.hcl

# 3. Create ECR repos first (images must exist before ECS/Lambda can be created)
terraform apply -target=module.ecr -var-file=environments/dev.tfvars

# 4. Push initial images to ECR, then set app_image and worker_image in dev.tfvars

# 5. Full apply
terraform apply -var-file=environments/dev.tfvars

# 6. Populate GitHub environment vars
terraform output
```

### Secrets management

All sensitive values are generated by Terraform and stored in AWS Secrets Manager:
- `DATABASE_URL` — constructed from RDS endpoint + random password; injected into ECS containers via the `secrets` field in the task definition (not environment variables)
- `JWT_SECRET_KEY` — 64-char random string
- `SECRET_KEY` (Django) — 64-char random string

Secrets are injected at container startup by the ECS agent using the task execution role. The app code reads them as plain environment variables (`os.environ["DATABASE_URL"]`) — no Secrets Manager SDK calls needed in app code.

### IAM roles

| Role | Principal | Permissions |
|---|---|---|
| `ecs-task-execution` | ECS agent | ECR pull, CloudWatch logs, read specific Secrets Manager ARNs |
| `ecs-task` | Django app | S3 read/write (media bucket), SQS send/receive, CloudWatch logs |
| `lambda` | Lambda service | SQS consume, S3 read/write, Secrets Manager read, VPC networking |
| `github-actions` | GitHub OIDC | ECR push, ECS update, Lambda update, register task def, read/write state bucket, DynamoDB lock |

The GitHub Actions role uses OIDC — no long-lived AWS credentials are stored in GitHub. The trust policy is scoped to the specific repo and the `main`/`develop` branches only.

### Security group rules

| From | To | Port | Protocol |
|---|---|---|---|
| Internet | ALB | 80, 443 | TCP |
| ALB | ECS tasks | 5000 | TCP |
| ECS tasks | RDS | 5432 | TCP |
| ECS tasks | Redis | 6379 | TCP |
| ECS tasks | Internet | 443 | TCP (outbound: ECR, Secrets Manager, CloudWatch) |
| Lambda | RDS | 5432 | TCP |
| Lambda | Redis | 6379 | TCP |
| Lambda | Internet | 443 | TCP (outbound: AWS APIs) |

ECS tasks and Lambda have no inbound rules from the internet. RDS and Redis have no outbound rules.

### Lifecycle rules

- `aws_ecs_service`: `ignore_changes = [task_definition, desired_count]` — CI/CD manages these after initial deploy
- `aws_lambda_function`: `ignore_changes = [image_uri]` — CI/CD manages this
- `aws_s3_bucket` (state bucket in bootstrap): `prevent_destroy = true`
- `aws_dynamodb_table` (lock table in bootstrap): `prevent_destroy = true`
