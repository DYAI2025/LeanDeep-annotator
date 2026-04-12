# RB-standard-deploy

**Trigger**: New code ready for production deployment
**Severity**: P2 (Planned)
**Estimated Duration**: 10 minutes
**Owner**: DevOps / Engineer

## Prerequisites

- [ ] All tests pass: `python3 -m pytest tests/ -x -q`
- [ ] Smoke test script exists: `scripts/smoke_test.sh`
- [ ] Railway project linked: `railway link` (one-time setup)
- [ ] All environment variables set on Railway

## Steps

### 1. Pre-Deploy Checks

```bash
# Run full test suite
python3 -m pytest tests/ -x -q

# Run eval corpus (marker detection quality)
python3 tools/eval_corpus.py

# Build Docker image locally
docker build -t leandeep:test .

# Run container and verify health
docker run -d --name leandeep-check -p 8420:8420 leandeep:test
sleep 5
curl -s http://localhost:8420/v1/health | jq .
docker stop leandeep-check && docker rm leandeep-check
```

### 2. Deploy

```bash
# Push latest code
git push origin main

# Deploy to Railway
railway up

# Watch build logs
railway logs
```

### 3. Post-Deploy Verification

```bash
# Get deployment URL
DEPLOY_URL=$(railway domain)

# Run smoke tests
BASE_URL="https://${DEPLOY_URL}" bash scripts/smoke_test.sh

# Manual verification
curl -s "https://${DEPLOY_URL}/v1/health" | jq .
curl -s "https://${DEPLOY_URL}/v1/engine/config" | jq '.total_markers'

# Test analysis endpoint with minimal payload
curl -s -X POST "https://${DEPLOY_URL}/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test.", "language": "en"}' | jq '.markers | length'
```

### 4. Monitor

```bash
# Watch logs for errors (first 5 minutes)
railway logs --follow

# Check Railway dashboard for CPU/memory/health
# Open: https://railway.app/project/<project-id>
```

### 5. Document

- Record deployment in `4-deploy/deployment-log.md` (date, commit hash, notes)
- Announce to team (Slack/email)

## Rollback

If verification fails:

1. Go to Railway dashboard → Deployments → Select previous successful build → Redeploy
2. Verify: `curl https://<service>.up.railway.app/v1/health`
3. Assess damage: check logs for any corrupted state
4. Document rollback reason in deployment log
