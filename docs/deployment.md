# Deployment guide

## Compose

`infra/docker/docker-compose.yml` runs the API, worker, frontend, and pgvector database. Use `infra/docker/smoke.ps1` on a machine with Docker Desktop to render the configuration, build the images, wait for `/health`, and remove the temporary stack and volume.

The smoke script uses local-only credentials when environment variables are absent. Do not reuse those values outside local development.

## Kubernetes

`infra/kubernetes/hr-tool.yaml` contains API and worker deployments, frontend deployment, services, a migration job, a pgvector integration stateful set, a secret reference, health probes, and API autoscaling. Supply real image tags and secret values through the deployment system. Never commit credentials.

Validate syntax and Kubernetes schema without contacting a cluster:

```powershell
./infra/kubernetes/validate.ps1
```

The pgvector stateful set is a development integration option. Production deployments should use an approved managed PostgreSQL/pgvector service with backups, encryption, network policy, and tested restore procedures.
