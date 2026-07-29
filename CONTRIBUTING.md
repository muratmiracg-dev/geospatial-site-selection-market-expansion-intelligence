# Contributing

1. Open an issue that states the analytical or engineering change and expected
   acceptance criteria.
2. Branch from a current `main`.
3. Keep generated commercial data synthetic and deterministic.
4. Add or update tests, data contracts, documentation and ADRs when behavior changes.
5. Run `make all` and attach any changed analytical metrics to the pull request.
6. Request review from the owners in `.github/CODEOWNERS`.

Changes that alter CRS, network assumptions, model targets, score weights, optimizer
constraints or business interpretation require analytical-owner approval. Do not
commit secrets, personal data, proprietary addresses or real customer/device records.

Pull requests should remain small enough to review and must explain whether generated
artifacts changed. A metric change without a documented causal explanation is not
ready to merge.

