param(
    [Parameter(Mandatory=$true)][string]$Source,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-z0-9][a-z0-9-]{1,62}$')][string]$CollectionId,
    [switch]$Execute
)
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$sourcePath = (Resolve-Path -LiteralPath $Source).Path
$destination = Join-Path $repo ("imports\" + $CollectionId)
if ($sourcePath -eq $destination) { throw "Source and destination must be different." }
$manifest = Get-Content -Raw -LiteralPath (Join-Path $repo 'imports\collections.json') | ConvertFrom-Json
if (-not ($manifest.collections | Where-Object { $_.id -eq $CollectionId })) {
    throw "CollectionId '$CollectionId' is not in imports/collections.json. Add it first."
}
$srcJson = Join-Path $sourcePath 'result.json'
if (-not (Test-Path -LiteralPath $srcJson -PathType Leaf)) {
    throw "Missing result.json at $srcJson"
}
Write-Host "Source: $sourcePath"
Write-Host "Target: $destination"
Write-Host "Mode: $(if ($Execute) {'COPY'} else {'DRY RUN'})"
$files = Get-ChildItem -LiteralPath $sourcePath -Recurse -File -Force |
  Where-Object { $_.FullName -notmatch '(?i)[\\/](\.git|node_modules)[\\/]' }
$bytes = ($files | Measure-Object -Property Length -Sum).Sum
Write-Host ("Detected {0} files, {1:N2} GiB" -f $files.Count, ($bytes / 1GB))
if (-not $Execute) {
    Write-Host "DRY RUN only. To copy, run again with -Execute."
    exit 0
}
New-Item -ItemType Directory -Force -Path $destination | Out-Null
# Robocopy preserves the internal folder layout without copying nested .git repositories.
& robocopy.exe $sourcePath $destination /E /R:1 /W:1 /XD '.git' 'node_modules' /XF 'Thumbs.db' '.DS_Store' /NFL /NDL /NP
$rc = $LASTEXITCODE
if ($rc -ge 8) { throw "Robocopy failed with exit code $rc" }
if (-not (Test-Path -LiteralPath (Join-Path $destination 'result.json'))) { throw "Staged result.json is missing" }
Write-Host "Staged $CollectionId successfully."
Write-Host "Next: python tools/build_multi_catalog.py --check-only"
Write-Host "Then: python tools/build_multi_catalog.py"
Write-Host "Media folders are intentionally ignored by Git. Upload images to S3 during AWS deployment."
