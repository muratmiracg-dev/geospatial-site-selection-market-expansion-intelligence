# API Reference

Run with:

```bash
uvicorn site_intelligence.api.app:app --host 0.0.0.0 --port 8000
```

Interactive OpenAPI documentation is available at `/docs`.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | run and artifact readiness |
| GET | `/v1/candidates` | ranked candidate summary |
| GET | `/v1/candidates/{candidate_id}` | full candidate and contributions |
| POST | `/v1/score` | recompute one candidate with bounded weights |
| POST | `/v1/scenarios/evaluate` | return a precomputed scenario portfolio |
| GET | `/metrics` | Prometheus exposition |

The service reads packaged artifacts and does not mutate data or approve a location.
Unknown candidates return 404. Invalid or negative weights return 422. Weight values
are normalized to one after validation.

Example:

```bash
curl -s http://localhost:8000/v1/candidates?limit=5
curl -s http://localhost:8000/v1/candidates/C24
curl -s -X POST http://localhost:8000/v1/score \
  -H 'content-type: application/json' \
  -d '{"candidate_id":"C24"}'
```

Any production deployment should add authentication, TLS, ingress rate limiting and
request correlation IDs.
