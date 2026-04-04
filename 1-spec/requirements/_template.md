# REQ-CLASS-short-name

**Class**: Functional | Performance | Security | Reliability | Usability | Maintainability | Portability | Scalability | Compliance  
**Priority**: Must-have | Should-have | Could-have  
**Status**: Draft | Approved | Implemented | Deprecated

## Requirement

Clear, testable statement. Use measurable language, not vague adjectives.

**Good**: "Detection latency for /v1/analyze/conversation must be < 500ms at p95 with 10-message input."  
**Bad**: "The system should be fast."

## Acceptance Criteria

- [ ] Test case 1 passes
- [ ] Test case 2 passes
- [ ] Performance metric verified

## Related Artifacts

- User Story: [US-xxx](../user-stories/US-xxx.md)
- Goal: [GOAL-yyy](../goals/GOAL-yyy.md)

## Design Notes

Which design document section addresses this? Link to [2-design/architecture.md](../../2-design/architecture.md) or other.

## Test Plan

How is this requirement validated?
- Unit test: `tests/test_xxx.py::test_yyy`
- Integration test: `tests/test_integration_xxx.py`
- E2E test: `tests/test_api_xxx.py`

## Notes

Additional context, dependencies, assumptions, open questions.
