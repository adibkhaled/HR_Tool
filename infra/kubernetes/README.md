# Kubernetes deployment

`hr-tool.yaml` is a schema-valid deployment template with placeholder secrets. Run `./infra/kubernetes/validate.ps1` with `kubectl` installed. It performs client-side validation only and does not prove cluster admission, image availability, migrations, or runtime readiness.
