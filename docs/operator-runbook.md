# Operator runbook

## Signals

Inspect `/health` for process liveness, `/ready` for configured dependency readiness, and `/metrics` for request latency, queue depth, processing failures, match volume, retrieval records, and grounded-result counts. Grafana dashboard JSON is in `grafana/hr-tool-overview.json`.

Use the `X-Correlation-ID` response header to join API logs, processing operation records, worker diagnostics, and audit events. Logs must remain free of document text, tokens, passwords, and provider payloads.

## Failure handling

- A failed processing operation is visible through its operation ID and remains retryable at the repository boundary.
- Provider timeout or malformed-output behavior must be tested with fakes before changing retry policy.
- Inspect queue depth and dependency readiness before restarting workers.
- Preserve completed match snapshots and audit history during rollback.

## Rollback

Disable new matching at the ingress or feature-flag layer, deploy the known-good API and worker images, reconcile queued operations, and verify `/health`, `/ready`, and audit correlation before re-enabling matching. This repository does not claim a staging rollback was executed locally.
