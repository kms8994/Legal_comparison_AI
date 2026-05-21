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

    & $python -c "from app.db.session import SessionLocal; from sqlalchemy import text; from pathlib import Path; db=SessionLocal(); db.execute(text(Path('../supabase/collection_requests.sql').read_text(encoding='utf-8'))); db.execute(text(Path('../supabase/collection_request_seed.sql').read_text(encoding='utf-8'))); db.commit(); db.close(); print('collection_queue=applied')"
}
finally {
    Pop-Location
}
