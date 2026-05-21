$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$backendDir = Join-Path $repoRoot "backend"

Push-Location $backendDir
try {
    $python = "python"
    $venvPython = Join-Path $backendDir ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        $python = $venvPython
    }

    & $python -c "from app.db.session import SessionLocal; from sqlalchemy import text; db=SessionLocal(); tables=['precedents','precedent_structures','processing_jobs','comparison_feedback']; [print(t + '=' + str(db.execute(text('select count(*) from ' + t)).scalar_one())) for t in tables]; db.close()"
}
finally {
    Pop-Location
}
