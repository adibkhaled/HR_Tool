$ErrorActionPreference = "Stop"

$env:POSTGRES_PASSWORD = if ($env:POSTGRES_PASSWORD) { $env:POSTGRES_PASSWORD } else { "local-only-password" }
$env:JWT_SECRET = if ($env:JWT_SECRET) { $env:JWT_SECRET } else { "local-only-jwt-secret-change-me" }

docker compose -f infra/docker/docker-compose.yml config | Out-Null
docker compose -f infra/docker/docker-compose.yml up -d --build
try {
    $deadline = (Get-Date).AddMinutes(3)
    do {
        try {
            $health = Invoke-RestMethod http://localhost:8000/health
            if ($health.status -eq "ok") { break }
        } catch { }
        if ((Get-Date) -gt $deadline) { throw "API health check timed out" }
        Start-Sleep -Seconds 3
    } while ($true)
    Invoke-RestMethod http://localhost:8000/health
} finally {
    docker compose -f infra/docker/docker-compose.yml down --volumes
}
