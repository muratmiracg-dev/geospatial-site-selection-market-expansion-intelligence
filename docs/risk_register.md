# Risk Register

| ID | Risk | Likelihood | Impact | Control / treatment | Owner | Residual |
|---|---|---|---|---|---|---|
| R01 | Synthetic metrics mistaken for real forecast | Medium | High | persistent labels, model card, human gate | Business | Medium |
| R02 | H3 network misstates travel time | High | High | straight-vs-network disclosure; independent routing | Analytical | Medium |
| R03 | Wrong CRS/coordinates | Low | High | EPSG contract, range and geometry tests | Data | Low |
| R04 | Candidate/POI spatial coverage gap | Medium | Medium | spatial-join warning ledger and extent review | Data | Medium |
| R05 | Spatial leakage inflates accuracy | Low | High | 12 km block GroupKFold and OOF metrics | Analytical | Low |
| R06 | Income/access proxies create geographic bias | Medium | High | contribution review, sensitivity and equity overlay | Business | Medium |
| R07 | AHP weights encode unchallenged preference | Medium | Medium | direction/weight ledger, CR and 750-draw sensitivity | Analytical | Low |
| R08 | Optimizer hides infeasibility or overlap | Low | High | terminal status, unique coverage and distance checks | Analytical | Low |
| R09 | Economic assumptions drift | High | High | binding-quote field gate and scenario stress | Business | Medium |
| R10 | Artifact/run mismatch | Low | High | manifest, run summary and immutable release set | Platform | Low |
| R11 | API abuse or malformed weights | Medium | Medium | schema bounds, read-only service, rate-limit at ingress | Platform | Low |
| R12 | Dependency/container vulnerability | Medium | High | Dependabot, pip-audit, CodeQL and Trivy workflow | Security | Medium |
| R13 | Secrets in repository or logs | Low | High | env injection, examples only, secret review | Platform | Low |
| R14 | PBIP renders differently in Desktop | Medium | Medium | starter label and Desktop acceptance test | BI | Medium |
| R15 | GitHub CI differs from local environment | Medium | Medium | pinned Python/deps; observe terminal checks after publish | Platform | Medium |

The risk owner updates treatment status at each analytical release. Medium/high residual
risks require explicit acceptance before production use.

