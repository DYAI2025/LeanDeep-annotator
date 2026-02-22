---
description: Systematic bug analysis using Socratic method — fix, upgrade to feature, or reveal deeper bugs
allowed-tools: Bash, Read, Glob, Grep, Edit, Write, AskUserQuestion, Task
---

# Bug Brainstorming: From Symptoms to Solutions

## Overview

Transform bug reports into deep, sustainable fixes through structured questioning and root cause exploration. Every bug is an opportunity: fix it, upgrade it to a feature, or follow it to reveal what's really broken.

**Core principle:** Ask questions to understand symptoms, trace root causes, evaluate fix strategies (fix vs. feature vs. deeper dig), implement, verify cascade effects.

**Announce at start:** "I'm using the Bug Brainstorm skill to systematically analyze this bug."

## The Process

### Phase 1: Symptom Understanding

- Check current project state (git status, recent changes, test results)
- Ask ONE question at a time to understand the bug
- Prefer multiple choice when possible
- Gather:
  - **What** is the observed behavior vs. expected behavior?
  - **When** does it happen? (always, sometimes, after specific action)
  - **Where** in the system? (endpoint, layer, component)
  - **Since when?** (recent change, always broken, regression)
- Attempt to reproduce the bug before proceeding
- If reproducible: capture exact input/output/error
- If not reproducible: gather more context (environment, data, timing)

### Phase 2: Root Cause Exploration

- Propose 2-3 hypotheses for the root cause
- For each hypothesis:
  - **Evidence for:** what observations support this?
  - **Evidence against:** what contradicts this?
  - **Diagnostic test:** one command/check to confirm or eliminate
- Ask: "Which hypothesis should we investigate first?"
- Run diagnostic tests to narrow down
- Trace the bug backward through the call chain:
  - Where does the wrong value first appear?
  - What produced it? What was the input?
  - Is the bug in the data, the logic, or the assumption?

### Phase 3: Fix Strategy

Present 2-3 approaches. For each bug, consider ALL THREE categories:

**A) Direct Fix** — Patch the immediate cause
- Scope: minimal change, lowest risk
- Trade-off: may leave underlying weakness intact

**B) Feature Upgrade** — The bug reveals a missing capability
- Scope: broader change, adds value
- Trade-off: more work, but eliminates the class of bug
- Examples: a regex FP becomes a context-aware filter; a missing validation becomes a schema guard; a race condition becomes a proper queue

**C) Deeper Investigation** — The bug is a symptom of something bigger
- Scope: diagnostic, may reveal additional bugs
- Trade-off: delays fix but prevents whack-a-mole
- Examples: one broken reference suggests the linking system is broken; one detection miss suggests the compiler has a gap

Present in 200-300 word sections per approach.
Ask: "Which strategy fits this bug? Or should we combine approaches?"

### Phase 4: Implementation

When strategy is approved:
1. Write or describe the fix in detail before applying
2. Show the exact changes (file, line, before/after)
3. Ask: "Does this change look correct?" before editing
4. Apply the fix
5. Run relevant tests immediately
6. If tests fail: don't force — go back to Phase 2

### Phase 5: Cascade Check & Verification

**This phase is critical — it's where bugs reveal other bugs.**

1. **Verify the fix:**
   - Does the original symptom disappear?
   - Do all existing tests pass?
   - Does the fix handle edge cases?

2. **Check for cascade effects:**
   - Did fixing this change behavior elsewhere?
   - Are there similar patterns in the codebase that have the same bug?
   - Run: `grep -r` for the same anti-pattern in related files

3. **Assess newly revealed bugs:**
   - Ask: "Now that we fixed X, I notice Y may also be affected. Should we:"
     - **a)** Fix Y now (if small and related)
     - **b)** Log Y as a separate issue (if large or different scope)
     - **c)** Investigate Y deeper (if it suggests a systemic problem)

4. **Update knowledge:**
   - If the bug class is new: note the pattern for future detection
   - If it's a known class: check if the existing guard should be strengthened

## When to Revisit Earlier Phases

**You can and should go backward when:**
- Diagnostic test disproves all hypotheses in Phase 2 → Return to Phase 1 for more symptoms
- Fix strategy feels like a band-aid → Return to Phase 2 for deeper root cause
- Implementation reveals the bug is different than hypothesized → Return to Phase 2
- Cascade check finds the real bug is elsewhere → Start new Phase 1 for that bug
- Partner provides new context at any point → Incorporate and re-evaluate

**Don't force forward linearly** when going backward would give better results.

## Bug Classification (for tracking)

After resolution, classify the bug:

| Type | Description | Example |
|------|-------------|---------|
| **Surface** | What you see is what you fix | Typo in regex, wrong config value |
| **Structural** | Fix requires architectural change | Missing input validation layer |
| **Systemic** | One instance of a class of bugs | All parsers skip edge case X |
| **Latent** | Revealed by fixing another bug | Auth fix exposes rate limiter gap |
| **Opportunity** | Bug that becomes a feature when fixed properly | Error handler → retry with backoff |

## Remember

- One question per message during Phase 1
- Always reproduce before theorizing
- Explore 2-3 hypotheses before committing to one
- Every bug gets the 3-way evaluation: fix / feature / deeper
- Present incrementally, validate as you go
- Cascade check is not optional — bugs travel in packs
- Go backward when needed — flexibility > rigid progression
- Announce skill usage at start
