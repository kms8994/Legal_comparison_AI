param(
    [string]$Query = "교통사고",
    [int]$Pages = 1,
    [int]$Display = 10,
    [double]$Sleep = 0.2
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$backendDir = Join-Path $repoRoot "backend"
$envPath = Join-Path $backendDir ".env"

if (-not (Test-Path $envPath)) {
    throw "backend/.env 파일이 없습니다. DATABASE_URL과 LAW_OPEN_API_OC를 먼저 설정해 주세요."
}

Push-Location $backendDir
try {
    $python = "python"
    $venvPython = Join-Path $backendDir ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        $python = $venvPython
    }

    & $python -m pipelines.collector.collect_precedents `
        --query $Query `
        --pages $Pages `
        --display $Display `
        --sleep $Sleep
}
finally {
    Pop-Location
}
