# RB-high-error-rate

**Trigger**: Error rate > 5% on `/v1/analyze` or any endpoint
**Severity**: P1 (Critical)
**Estimated Duration**: 15 minutes
**Owner**: On-call Engineer

## Steps

### 1. Verify the Problem

```bash
# Check health endpoint
curl -s https://<service>.up.railway.app/v1/health | jq .

# Check recent logs for error patterns
railway logs --tail 200 | grep -i "error\|exception\|500\|traceback"

# Check Railway dashboard for error rate graph
# Look for: 5xx responses, crash loops, OOM kills
```

### 2. Isolate the Cause

**Decision Tree**:

- **If logs show `marker_registry.json` load failure** → Go to [RB-marker-registry-corruption](RB-marker-registry-corruption.md)
- **If logs show LLM provider timeout/errors** → Go to [RB-semantic-provider-outage](RB-semantic-provider-outage.md)
- **If logs show Redis connection errors** → Go to [RB-redis-connection-failure](RB-redis-connection-failure.md)
- **If logs show validation errors (400s)** → Check recent API contract changes
- **If logs show 500s with no clear pattern** → Check recent deployment, consider rollback

### 3. Mitigate

**Immediate action** (if cause unclear):

```bash
# Rollback to last known good deployment
# Railway Dashboard → Deployments → Redeploy previous version

# OR restart the service
railway restart
```

**If cause is identified**:

- Fix the root cause (code fix, config change, etc.)
- Test locally: `docker build -t leandeep:test . && docker run -p 8420:8420 leandeep:test`
- Deploy fix: `railway up`

### 4. Verify Fix

```bash
# Wait for deployment
sleep 60

# Run smoke tests
BASE_URL="https://<service>.up.railway.app" bash scripts/smoke_test.sh

# Monitor error rate for 5 minutes
railway logs --follow | grep -c "error"
```

### 5. Document

- Record incident in deployment log
- If recurring, create permanent fix in next sprint
