# GitHub Branch Protection Guide

Apply these rules to `main` after the repository is published and the workflow job
names are observed exactly.

## Recommended rules

- Require a pull request before merging.
- Require at least one approving review.
- Dismiss stale approvals when new commits are pushed.
- Require review from CODEOWNERS.
- Require conversation resolution.
- Require status checks to pass and branch to be current.
- Block force pushes and deletion.
- Require signed commits where organizational policy supports them.
- Restrict bypass to emergency administrators and audit every bypass.
- Enable secret scanning, push protection, Dependabot alerts and private
  vulnerability reporting.

## Intended required checks

- `CI / lint`
- `CI / tests`
- `CI / artifact-smoke`
- `CodeQL / Analyze (python)`
- `Security / pip-audit`
- `Security / trivy`

GitHub can display job names differently after the first run. Select the exact terminal
check names shown by the repository; do not configure guessed names. The first
publication stage must observe all workflows to completion before finalizing this list.

