param(
    [Parameter(Mandatory = $true)] [string] $ProjectId,
    [Parameter(Mandatory = $true)] [string] $Region,
    [string] $Repository = "adaptive-offers",
    [string] $Service = "adaptive-offers-demo",
    [string] $ImageTag = "readonly-latest",
    [switch] $AllowUnauthenticated
)

$ErrorActionPreference = "Stop"
$image = "$Region-docker.pkg.dev/$ProjectId/$Repository/$Service`:$ImageTag"

Write-Host "Construindo imagem local: $image"
docker build --tag $image .
if ($LASTEXITCODE -ne 0) { throw "A construção da imagem falhou." }

gcloud auth configure-docker "$Region-docker.pkg.dev" --quiet
if ($LASTEXITCODE -ne 0) { throw "A configuração do Docker para o Artifact Registry falhou." }

docker push $image
if ($LASTEXITCODE -ne 0) { throw "O envio para o Artifact Registry falhou." }

$deployArgs = @(
    "run", "deploy", $Service,
    "--project", $ProjectId,
    "--region", $Region,
    "--image", $image,
    "--port", "8080",
    "--set-env-vars", "APP_ENV=cloud-run,POLICY_MODE=readonly,STATE_PATH=/tmp/policy.json,SNAPSHOT_PATH=/app/config/policy_snapshot.json,DATABASE_PATH=/tmp/readonly.db",
    "--min", "0",
    "--max", "1",
    "--concurrency", "4",
    "--cpu", "1",
    "--memory", "512Mi"
)
if ($AllowUnauthenticated) { $deployArgs += "--allow-unauthenticated" }
else { $deployArgs += "--no-allow-unauthenticated" }

gcloud @deployArgs
if ($LASTEXITCODE -ne 0) { throw "A publicação no Cloud Run falhou." }

Write-Host "Publicação somente leitura concluída. O feedback permanece desabilitado no modo readonly."
