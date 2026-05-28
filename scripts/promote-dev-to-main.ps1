param(
    [switch]$SkipChecks
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$status = git status --porcelain
if ($status) {
    Write-Host "Working tree is not clean:"
    git status --short
    throw "Commit, stash, or remove local changes before promotion."
}

git fetch origin main dev
git switch main
git pull --ff-only origin main

try {
    git merge --ff-only dev
}
catch {
    git merge --no-ff dev -m "Merge dev into main"
}

if (-not $SkipChecks) {
    python -m compileall backend/app
    Push-Location frontend
    try {
        node .\node_modules\vite\bin\vite.js build
    }
    finally {
        Pop-Location
    }
}

git push origin main
git status --short --branch
