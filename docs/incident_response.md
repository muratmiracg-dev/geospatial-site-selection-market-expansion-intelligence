# Incident Response

## Phases

1. **Detect and classify:** record time, reporter, affected component, run/version,
   symptoms and potential decision impact.
2. **Contain:** disable unsafe outputs, isolate credentials/data sources and preserve
   logs, manifests and generated artifacts.
3. **Investigate:** reproduce on an immutable input copy; identify data, model,
   optimizer, code or operational root cause.
4. **Remediate:** implement the smallest reviewed fix, regenerate affected outputs and
   execute all quality gates.
5. **Recover:** restore only an approved, hash-verified artifact set.
6. **Learn:** publish a blameless post-incident review with actions, owners and dates.

## Decision-specific controls

If an incident could change candidate ranking or selected portfolio, label all affected
reports “withdrawn,” notify the analytical and business owners, and require a new
review. Never silently replace an already reviewed output.

## Minimum incident record

- incident ID, severity and timeline;
- affected data/model/code/endpoint and commit;
- candidate/portfolio decisions potentially affected;
- containment and recovery evidence;
- root cause and contributing controls;
- corrective/preventive actions;
- final approval and communication log.

## Examples

- wrong CRS produces distorted distances;
- new candidates fall outside the network graph;
- candidate score weights do not sum to one;
- optimizer returns infeasible but stale results remain visible;
- report combines metrics from different runs;
- a secret appears in logs or a published artifact.

