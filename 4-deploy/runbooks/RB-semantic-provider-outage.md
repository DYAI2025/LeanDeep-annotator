# RB-semantic-provider-outage

**Trigger**: Gemini API (or configured semantic provider) returning 5xx errors or timeouts
**Severity**: P2 (High)
**Estimated Duration**: 10 minutes
**Owner**: On-call Engineer

## Steps

### 1. Verify the Problem

```bash
# Check logs for provider errors
railway logs --tail 100 | grep -i "gemini\|provider\|timeout\|503\|502"

# Check if responses include degraded: true
curl -s -X POST "https://<service>.up.railway.app/v1/analyze/conversation" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "A", "text": "Test"}]}' | jq '.degraded, .provider_used, .fallback_reason'
```

### 2. Isolate the Cause

- **If Gemini status page shows outage** → External issue, use fallback
- **If API key expired/invalid** → Check `LEANDEEP_GOOGLE_API_KEY` on Railway
- **If rate limited** → Check `LEANDEEP_RATE_LIMIT_PER_MINUTE` and traffic patterns

### 3. Mitigate

**Option A: System auto-fallback** (should happen automatically)
- The system should already fall back to embedding-based or markers-only mode
- Verify `degraded: true` is set in responses

**Option B: Switch provider** (if alternative configured)

```bash
# Change provider via Railway CLI
railway variables set LEANDEEP_LLM_PROVIDER="openrouter"
railway restart
```

**Option C: Increase timeout** (if provider is slow but working)

```bash
railway variables set LEANDEEP_LLM_TIMEOUT="5000"
railway restart
```

### 4. Monitor

- Watch error rate decrease after mitigation
- Monitor fallback quality (markers-only mode is less accurate)
- Check provider status page for resolution

### 5. Post-Incident

- If recurring, consider adding more providers to fallback chain
- Review if rate limits need adjustment
- Document in deployment log
