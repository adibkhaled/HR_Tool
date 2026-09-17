$ErrorActionPreference = "Stop"

kubectl apply --dry-run=client --validate=true -f infra/kubernetes/hr-tool.yaml
