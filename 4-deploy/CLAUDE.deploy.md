Phase-specific instructions for the **Deploy** phase. Extends [../CLAUDE.md](../CLAUDE.md).

## Purpose

This phase ships and operates the system. Infrastructure as code, deployment procedures, runbooks, monitoring.

For LeanDeep, deployment includes:
- **Railway infrastructure** (single service, multi-stage Dockerfile, environment variables) per DEC-railway-deployment
- API versioning and backward compatibility
- Monitoring and alerts (error rates, latency, marker coverage)
- Rollback procedures
- Runbooks for incident response

## Phase Artifacts

| Artifact | Location | Purpose |
|----------|----------|---------|
| Runbooks | [`runbooks/`](runbooks/) | Step-by-step incident response, maintenance, operational procedures |
| Deployment Scripts | `../railway.toml`, `../Dockerfile` | Infrastructure as code, container configuration |
| Legacy (deprecated) | `../fly.toml` | Kept for historical reference only (see DEC-railway-deployment) |
| Deployment Log | (In this directory, as needed) | Record of deployments, changes, rollbacks |

---

## Deployment Workflow

### Pre-Deployment Checklist

- [ ] All code phase tasks linked to requirements are Done
- [ ] Test suite passes (unit, integration, E2E)
- [ ] Eval corpus score acceptable (detection accuracy, latency)
- [ ] Documentation updated (`CLAUDE.md`, design docs, API docs)
- [ ] Breaking changes analyzed and communicated
- [ ] Rollback plan documented
- [ ] Monitoring and alerts configured

### Deployment to Railway

```bash
# 1. Build and test locally (replicates Railway's Docker build)
docker build -t leandeep:latest .
docker run --rm -p 8420:8420 leandeep:latest
curl http://localhost:8420/v1/health

python3 -m pytest tests/ -x -q

# 2. Run eval suite
python3 tools/eval_corpus.py
python3 tools/eval_dynamics.py

# 3. Deploy (after linking project once with `railway link`)
railway up

# 4. Verify deployment
curl https://<service>.up.railway.app/v1/health
railway logs
```

### Environment Variables

Set on Railway via CLI or dashboard. All `LEANDEEP_*` vars listed in root `CLAUDE.md` plus:

```bash
railway variables set LEANDEEP_GOOGLE_API_KEY=xxx
railway variables set LEANDEEP_SEMANTIC_PROVIDER=gemini
railway variables set LEANDEEP_CORS_ORIGINS=production-domain.com
railway variables set LEANDEEP_REQUIRE_AUTH=true
railway variables set LEANDEEP_SEMANTIC_MODEL=gemini-1.5-flash
```

Frontend note: Vite env vars (prefixed `VITE_*`) are baked in at build time, so changing them requires a redeploy. Current frontend uses no runtime env vars.

See [../CLAUDE.md](../CLAUDE.md) for all environment variables.

---

## Runbooks

Runbooks are procedural documents for common operational tasks.

### Runbook Template (`runbooks/_template.md`)

```markdown
# RB-incident-or-procedure-name

**Trigger**: When [symptom or condition]
**Severity**: P1 | P2 | P3 (Critical | High | Low)
**Estimated Duration**: X minutes
**Owner**: [role or team]

## Steps

1. **Verify the problem**
   - Check: [indicator or metric]
   - Command: `railway logs | grep error`
   - Expected: [what should be true if problem exists]

2. **Isolate the cause**
   - Check: [another indicator]
   - Decision tree: If X, then Y; if Z, then W

3. **Mitigate**
   - Action: [immediate fix or workaround]
   - Command: `railway up`
   - Verify: [how to confirm fix worked]

4. **Document and communicate**
   - Notify: [stakeholders]
   - Record: [what to document]

5. **Post-incident**
   - Root cause: [why did this happen]
   - Preventive: [what changes to prevent recurrence]

## Rollback

If mitigation made things worse:

1. Revert to previous version: `railway rollback` (or use dashboard → Deployments → Redeploy a prior build)
2. Verify: curl health check
3. Assess damage
```

### Example Runbooks (to be documented)

| Runbook | Severity | Trigger |
|---------|----------|---------|
| RB-high-error-rate | P1 | Error rate > 5% on /v1/analyze |
| RB-marker-registry-corruption | P1 | Engine fails to load marker_registry.json |
| RB-semantic-provider-outage | P2 | Gemini API returning 5xx |
| RB-redis-connection-failure | P2 | Redis unavailable (Pro tier degraded) |
| RB-rollback-procedure | (General) | Standard rollback workflow |
| RB-zero-downtime-deployment | (Planned) | Deployment with traffic shift |

---

## Monitoring and Alerts

### Key Metrics

| Metric | Alert Threshold | Action |
|--------|-----------------|--------|
| /v1/analyze error rate | > 5% | P1 runbook; check marker registry |
| /v1/analyze latency p95 | > 500ms | P2 runbook; check semantic provider |
| /v1/personas latency p95 | > 1000ms | P2 runbook; check Redis |
| Marker detection consistency | < 95% | P2 runbook; check corpus eval |
| Semantic provider latency p95 | > 2000ms | Consider provider fallback |

### Monitoring Implementation

- **Logs**: Structured JSON via FastAPI middleware; view via `railway logs` or dashboard
- **Metrics**: Prometheus-compatible endpoint (if applicable); Railway shows CPU/memory/network per service
- **Alerts**: Railway webhook integrations (Slack/Discord/email) + optional Datadog/NewRelic
- **Health check**: `GET /v1/health` — Railway hits this per `railway.toml`, auto-restarts on failure (3 retries)

---

## Versioning and Backward Compatibility

### API Versioning Strategy

- Current: **v1** (stable, no breaking changes planned in near term)
- Future: v2 if major architectural changes needed
- Deprecation: 6-month notice before sunset of any endpoint

### Backward Compatibility

- Marker schema: New fields are additive (never remove/rename fields in v1)
- SemanticProfile: New dimensions go to v2 or optional fields
- Persona storage: Maintain YAML format compatibility across minor versions
- Response format: Never change existing field meanings; add new fields as optional

### Migration Plan (if breaking change needed)

1. Document new v2 endpoint
2. Deploy alongside v1 (dual-route in `fly.toml` or router middleware)
3. Give consumers 6 months notice (in API docs and announcement)
4. Log deprecation warnings on v1 requests
5. Sunset v1 endpoint

---

## Decisions Relevant to This Phase

| File | Title | Trigger |
|------|-------|---------|
| (TBD) | Deployment frequency | When establishing release cadence |
| (TBD) | Rollback automation | When defining incident response |
| (TBD) | Monitoring targets | When setting up observability |

---

## Infrastructure as Code

### Railway Configuration (`../railway.toml`)

See existing `railway.toml` for:
- Build: `DOCKERFILE` builder, path `Dockerfile`
- Deploy: healthcheck `/v1/health` (timeout 10s), restart `ON_FAILURE` (max 3)
- Resources and scale settings configured via Railway dashboard
- Environment variables set via `railway variables set ...` (not in the TOML)

### Docker Configuration (`../Dockerfile`) — multi-stage per DEC-railway-deployment

Stage 1 — **Frontend build**:
- `node:20-alpine` base
- `npm ci` in `3-code/frontend/` + `npm run build` → produces `3-code/frontend/dist/`

Stage 2 — **Python runtime**:
- `python:3.12-slim` base
- Install `requirements.txt`
- Copy `api/`, `build/markers_normalized/`, `mcp_server.py`
- Copy frontend build output from stage 1 to `/app/frontend_dist/`
- `ENV PORT=8420`, `EXPOSE ${PORT}`
- Entrypoint: `uvicorn api.main:app --host 0.0.0.0 --port ${PORT}`

Requirements:
- Non-root user for security
- Optimized layer caching (dependency layers before source copy)
- Frontend served as static files from FastAPI at `/` (not `/playground`)

### Legacy (`../fly.toml`) — deprecated

Kept as historical reference only. Do **not** use for deployment. See DEC-railway-deployment for rationale.

---

## Post-Deployment

1. **Verification**
   - Check health endpoint
   - Run smoke tests (sample requests to each endpoint)
   - Monitor logs for errors

2. **Communication**
   - Announce deployment to stakeholders
   - Update deployment log

3. **Documentation**
   - Update version in `CLAUDE.md`
   - Document any breaking changes
   - Update runbooks if procedures changed

4. **Optimization**
   - Review metrics and logs
   - Note performance observations
   - Plan improvements for next cycle
