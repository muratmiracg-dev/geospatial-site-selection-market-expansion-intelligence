# Analytical Governance

## Decision rights

| Role | Accountability |
|---|---|
| Data owner | source approval, access, retention and data contract |
| Analytical owner | method, validation, score weights and model card |
| Platform owner | API, database, deployment, monitoring and incident response |
| Business owner | commercial assumptions and field-validation scope |
| Investment committee | final capital decision; cannot be delegated to the model |

## Stage gates

1. **Data gate:** provenance, license, CRS, geometry and contract checks pass.
2. **Model gate:** spatial validation, baseline comparison, residual review and model
   card approval.
3. **Decision gate:** score contributions, sensitivity, constraints and optimizer
   feasibility reviewed.
4. **Field gate:** exact site, legal access, routing, traffic, rent, capex and operating
   assumptions verified.
5. **Capital gate:** human committee approves, rejects or requests further evidence.

## Change classes

- **Standard:** documentation or non-behavioral refactor; normal review.
- **Analytical:** feature, weight, target, score or optimizer change; analytical and
  business review plus regenerated artifacts.
- **Data:** new source, license or geography; data-owner review and crosswalk update.
- **High risk:** personal data, automated authorization or production financial use;
  legal/security review and a new threat/privacy assessment.

## Evidence retention

Each approved run retains the configuration, data contract, processed inputs, model,
out-of-fold predictions, SHAP output, AHP specification, scenario selection, quality
ledger, tests, artifact manifest and reviewer sign-off. Metrics must never be copied
manually into dashboards without traceability to a run artifact.

