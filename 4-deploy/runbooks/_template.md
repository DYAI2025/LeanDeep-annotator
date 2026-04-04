# RB-incident-or-procedure-name

**Type**: Incident Response | Maintenance | Deployment | Troubleshooting  
**Severity**: P1 (Critical) | P2 (High) | P3 (Medium) | P4 (Low)  
**Estimated Duration**: X minutes  
**Owner**: [Role or Team]  
**Last Updated**: YYYY-MM-DD

## Trigger

When should this runbook be activated? What symptom or condition?

Example: "Error rate on /v1/analyze > 5% for > 5 minutes"

## Prerequisites

What must be true before following this runbook?

Example:
- Fly.io CLI installed and authenticated
- Access to production app secrets
- Understanding of marker registry format

## Immediate Actions (First 5 minutes)

1. **Verify the problem**
   ```bash
   # Check logs
   flyctl logs --app leandeep-prod | grep ERROR
   
   # Check error rate
   # (if monitoring is configured)
   ```
   Expected: See errors related to [specific component]

2. **Page on-call if needed**
   - If P1: Immediately notify [team]
   - If P2: Notify within 5 minutes

3. **Prevent escalation** (if applicable)
   - Action: [e.g., "Scale up to 2 instances"]
   - Command: `flyctl scale vm shared-cpu-2x --count 2`

---

## Diagnosis (5-15 minutes)

### Scenario 1: [Specific symptom]

Check:
```bash
# Diagnostic command 1
flyctl ssh console
> SELECT COUNT(*) FROM marker_registry;
```

If [condition], then proceed to "Solution 1: [Mitigation]"

### Scenario 2: [Another symptom]

Check:
```bash
# Diagnostic command 2
```

If [condition], then proceed to "Solution 2: [Mitigation]"

---

## Solutions

### Solution 1: [Mitigation for Scenario 1]

**Steps**:
1. [Action 1]
2. [Action 2]
3. [Action 3]

**Verification**:
```bash
curl https://leandeep-prod.fly.dev/v1/health
# Expected: {"status": "ok", "marker_count": XXXX}
```

**Rollback** (if solution makes things worse):
```bash
flyctl releases --image [previous-image-id]
# or
flyctl deploy --image [known-good-image]
```

### Solution 2: [Mitigation for Scenario 2]

**Steps**:
1. [Action 1]
2. [Action 2]

**Verification**: [How to confirm fix worked]

---

## Communication

1. **During incident**: Notify stakeholders in [Slack channel] every 10 minutes with status
2. **Resolution**: Post brief summary to [incident log channel]
3. **Post-mortem**: Schedule within 24 hours if P1

---

## Root Cause Analysis (Post-Incident)

1. **Timeline**: When did symptoms first appear? When was fix applied?
2. **Root cause**: Why did this happen?
3. **Contributing factors**: What made it worse or prevented early detection?
4. **Preventive actions**:
   - [ ] Code change: [description]
   - [ ] Monitoring addition: [description]
   - [ ] Documentation: [description]
   - [ ] Testing: [new test to prevent recurrence]
5. **Owner**: Who is responsible for preventive actions?
6. **Due date**: When must preventive actions be complete?

---

## References

- Architecture: [2-design/architecture.md](../../2-design/architecture.md)
- Health check: `GET /v1/health`
- Monitoring: [monitoring dashboard link]
- Related runbooks: [RB-related-incident](RB-related-incident.md)

---

## Revision History

| Date | Change | Author |
|------|--------|--------|
| YYYY-MM-DD | Initial version | [Name] |
