# Incident Response Guide

## Severity levels

| Level | Example | Response time |
|-------|---------|---------------|
| S1 | Data breach, total outage | Immediate |
| S2 | Readiness failing, auth broken | < 1 hour |
| S3 | Elevated errors, slow queries | < 4 hours |
| S4 | Single feature degraded | Next business day |

## Triage checklist

1. Confirm scope — all users or single tenant?
2. Check `/api/v1/health` component status
3. Collect `request_id` from affected API errors
4. Review recent deployments and migrations
5. Check Redis queue depth and worker logs

## Communication template

> Delphi experienced [brief description] between [UTC start] and [UTC end].
> Impact: [users/features affected].
> Root cause: [summary].
> Request IDs for support: [ids].

## Post-incident

- Write timeline with `request_id` correlation
- Add regression test if applicable
- Update runbook or ADR if architecture gap found

## Security incidents

For suspected credential compromise:

1. Rotate `DELPHI_JWT_SECRET_KEY`
2. Invalidate all refresh tokens (DB truncate `refresh_tokens`)
3. Force user re-login
4. Review `audit_logs` for `authorization_denied` spikes
