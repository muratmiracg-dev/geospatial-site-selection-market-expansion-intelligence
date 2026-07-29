# Security Policy

## Supported version

Only the latest `main` revision is supported.

## Reporting

Do not open a public issue for suspected vulnerabilities. Use GitHub private
vulnerability reporting after publication, or contact the repository owner through
the private channel listed in the repository profile.

Include the affected component, reproduction steps, impact, proposed severity and any
temporary mitigation. Do not include real secrets or personal data in the report.

## Security posture

- No production credentials are included.
- Containers run read-only where practical, drop Linux capabilities and use
  `no-new-privileges`.
- API inputs are schema validated and scoring weights are bounded.
- Dependency audit, CodeQL and container scanning workflows are defined.
- Synthetic data is still treated as untrusted input at ingestion boundaries.

See `docs/threat_model.md` and `docs/incident_response.md` for the detailed controls.

