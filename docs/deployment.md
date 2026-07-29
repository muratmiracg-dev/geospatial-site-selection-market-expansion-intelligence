# Deployment Guide

## Local

```bash
cp .env.example .env
docker compose up --build
```

Replace all example passwords. The compose stack includes PostGIS, FastAPI,
Prometheus and Grafana. The database network is internal.

## Kubernetes

The manifests in `k8s/` provide a two-replica API deployment, service, HPA,
PodDisruptionBudget and network policy. Before applying:

- build and sign an immutable image;
- replace the placeholder image reference;
- create a namespace and secrets outside Git;
- configure ingress TLS/authentication and rate limiting;
- provide approved artifact storage;
- configure resource limits, backups and monitoring retention;
- run SQL migrations through a controlled job.

## Release verification

1. verify image digest and artifact manifest;
2. apply schema/view SQL to a disposable database;
3. run `sql/validation.sql`;
4. check `/health`, `/v1/candidates?limit=1` and `/metrics`;
5. compare candidate count, top candidate and base scenario to the approved run;
6. confirm Prometheus scrape and Grafana dashboard;
7. retain rollback image and artifacts.

The included infrastructure is a production-oriented starting point, not a claim that
a cloud environment has been deployed.
