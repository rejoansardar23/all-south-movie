param(
    [Parameter(Mandatory=$true)][string]$Bucket,
    [Parameter(Mandatory=$true)][string]$DistributionId,
    [string]$SiteUrl = '',
    [switch]$Execute,
    [switch]$SkipMedia
)
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $repo
try {
    aws --version
    if ($LASTEXITCODE -ne 0) { throw "AWS CLI is not configured" }
    $args = @('tools/build_site.py')
    if ($SkipMedia) { $args += '--skip-media' }
    if ($SiteUrl) { $args += @('--site-url', $SiteUrl) }
    & python @args
    if ($LASTEXITCODE -ne 0) { throw "Site packaging failed" }
    $target = "s3://$Bucket/"
    if (-not $Execute) {
        Write-Host "DRY RUN: Preview S3 changes only. CloudFront will NOT be invalidated."
        & aws s3 sync dist $target --dryrun --cache-control 'public,max-age=3600'
        exit $LASTEXITCODE
    }
    Write-Host "Deploying to $target ..."
    & aws s3 sync dist $target --cache-control 'public,max-age=3600'
    if ($LASTEXITCODE -ne 0) { throw "S3 upload failed" }
    & aws cloudfront create-invalidation --distribution-id $DistributionId --paths '/index.html' '/assets/*' '/data/catalog.json'
    if ($LASTEXITCODE -ne 0) { throw "CloudFront invalidation failed" }
    Write-Host "Deployment submitted. Test the CloudFront domain after the invalidation completes."
} finally {
    Pop-Location
}
