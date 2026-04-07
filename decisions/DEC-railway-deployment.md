# DEC-railway-deployment

**Status**: Approved
**Date**: 2026-04-07
**Deciders**: Project owner
**Supersedes**: Implicit Fly.io default in `CLAUDE.deploy.md`

## Context

LeanDeep 6.0 needs a production deployment target. The repo currently has a basic `Dockerfile`, a legacy `fly.toml` (never actively used for production), and a minimal `railway.toml` stub. CLAUDE.md still states "Infrastructure: Fly.io deployment" but no active Fly.io deployment exists.

The project has two deployable artifacts:
- **Backend**: Python/FastAPI (`api/main.py`), port 8420, loads `build/markers_normalized/marker_registry.json` at startup
- **Frontend**: React/TypeScript/Vite SPA (`3-code/frontend/`), currently only runs via `npm run dev`

## Decision

**Use Railway as the primary production deployment platform** for LeanDeep 6.0, with a **single-service, monolithic deployment strategy**: one Railway service running a Dockerfile that (1) builds the frontend SPA during the Docker build stage, (2) copies the built assets into the FastAPI container, and (3) serves them as static files from FastAPI via a `StaticFiles` mount at `/`. The API continues to respond at `/v1/*`.

### Why Railway

- **Cost efficiency**: Single hobby service covers backend + frontend at ~$5/month baseline (vs. separate Fly.io apps or Vercel + Fly.io split)
- **Nixpacks/Dockerfile flexibility**: Dockerfile path works out of the box; no vendor-specific build config needed
- **Simple env var management**: secrets set per service via CLI or dashboard, no separate secrets command
- **Healthcheck support**: `railway.toml` already defines `/v1/health` as healthcheck path, matches FastAPI endpoint
- **Familiar to the maintainer**: DYAI VPS and other infra already use Railway for related projects

### Why single-service (monolithic)

- **Simplicity**: One deploy target, one DNS entry, one set of logs. No CORS config between frontend and backend (same origin).
- **Latency**: Frontend and API on the same host → no extra network hop
- **Lower cost**: One service instead of two
- **Trade-off accepted**: Frontend cannot scale independently of backend. Acceptable since:
  - Frontend is a small static SPA (~70KB gzipped)
  - Both scale vertically with the same traffic profile (one request → one frontend hit + several API calls)
  - If this becomes a bottleneck later, splitting is straightforward (frontend to Vercel, backend stays on Railway)

### Why NOT Fly.io / Vercel / AWS

- **Fly.io**: Equivalent capability but historically harder env var management and more expensive once machines run continuously. No existing active Fly deployment to protect.
- **Vercel**: Excellent for frontend-only, but requires splitting backend to a separate provider (Railway or otherwise), adding complexity.
- **AWS/GCP**: Overkill for current scale. Revisit if production load justifies the operational overhead.

## Consequences

### Positive
- Single `railway.toml` + `Dockerfile` is the full deployment contract
- Existing `railway.toml` healthcheck path already matches `/v1/health` → no config churn
- Frontend build artifacts versioned with backend → atomic deploys, no frontend/backend version skew
- FastAPI already serves static files (existing `/playground` route) → pattern extends naturally

### Negative
- **Dockerfile grows**: needs a multi-stage build (Node for frontend build, Python for runtime)
- **Build time increases**: ~30-60 seconds added for `npm install` + `npm run build`
- **No independent frontend rollback**: rolling back the API also rolls back the UI (mitigated by atomic deploys — usually you want them together anyway)
- **Frontend env vars**: Vite bakes env vars at build time, so runtime env var changes require a rebuild. Not a regression vs. current state.

### Neutral
- `fly.toml` becomes dead code. Decision: **keep it** as a historical reference but add a comment at the top noting it is deprecated. Do NOT delete — removing infrastructure as code files without history leaves no audit trail if we ever need to compare platforms again.

## Scope of impact

- **Modifies**: `Dockerfile` (multi-stage build), `railway.toml` (may need more config), `4-deploy/CLAUDE.deploy.md` (workflow), `CLAUDE.md` (Infrastructure line)
- **Creates**: Deploy tasks in `3-code/tasks.md` Phase 3e
- **Doesn't touch**: `api/`, `3-code/frontend/src/`, tests, any application code

## Implementation checklist

The following work is tracked as Deploy-phase tasks in `3-code/tasks.md`:

1. `TASK-deploy-dockerfile-multistage` — multi-stage Dockerfile (Node build → Python runtime)
2. `TASK-deploy-static-serving` — extend FastAPI to serve frontend dist at `/`
3. `TASK-deploy-railway-config` — finalize `railway.toml` (restart policy, env vars list, resources)
4. `TASK-deploy-env-vars-setup` — document + set all `LEANDEEP_*` and `GEMINI_API_KEY` on Railway
5. `TASK-deploy-smoke-tests` — post-deploy smoke test script
6. `TASK-deploy-runbook-initial` — first runbook: standard deploy + rollback

## Revisit conditions

Revisit this decision if:
- Monthly Railway cost exceeds $30 at current traffic → evaluate Fly.io or Vercel+Railway split
- Frontend traffic dominates backend load → split to Vercel (static CDN is cheaper at scale)
- Need for geographic distribution (EU + US) → Railway's regions are limited vs. Fly.io's global anycast
