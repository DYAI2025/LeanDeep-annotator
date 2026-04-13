# RB-rollback

**Trigger**: Deployment caused errors, degraded performance, or incorrect behavior
**Severity**: P1 (Critical)
**Estimated Duration**: 5 minutes
**Owner**: DevOps / Engineer

## Steps

### 1. Confirm the Problem

```bash
# Check health endpoint
curl -s https://<service>.up.railway.app/v1/health | jq .

# Check recent logs for errors
railway logs --tail 100 | grep -i "error\|exception\|traceback"

# Check Railway dashboard for crash loops or high error rates
```

### 2. Rollback

```bash
# Option A: Railway Dashboard (recommended)
# 1. Open https://railway.app/project/<project-id>
# 2. Click "Deployments" tab
# 3. Find last known good deployment
# 4. Click "..." → "Redeploy"

# Option B: CLI (if available)
railway rollback
```

### 3. Verify Rollback

```bash
# Wait for deployment to complete (check Railway dashboard)
sleep 60

# Verify health
curl -s https://<service>.up.railway.app/v1/health | jq .

# Run smoke tests
BASE_URL="https://<service>.up.railway.app" bash scripts/smoke_test.sh

# Test core functionality
curl -s -X POST "https://<service>.up.railway.app/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test after rollback.", "language": "en"}' | jq '.markers | length'
```

### 4. Assess Damage

- Check if any persistent data was corrupted (personas, enrichment queues)
- Review logs for any side effects during the bad deployment
- Check if any users were affected (error rate spike, latency increase)

### 5. Document and Communicate

- Record rollback in `4-deploy/deployment-log.md` (date, reason, commit rolled back to)
- Notify team of the incident
- Create incident report if user-facing impact occurred

## Post-Incident

1. **Root Cause Analysis**: Why did the bad deployment pass tests?
2. **Preventive Measures**: What additional checks are needed?
3. **Fix and Redeploy**: Address the root cause, re-test, deploy again
