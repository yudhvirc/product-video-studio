# Installs (or updates) the product-video-studio Claude Code plugin without git.
# Downloads the latest release zip and extracts it into %USERPROFILE%\.claude\skills\,
# where Claude Code loads it in every session (as product-video-studio@skills-dir).
#
#   irm https://raw.githubusercontent.com/yudhvirc/product-video-studio/main/install.ps1 | iex
#
# An existing copy is moved to %TEMP% (not deleted, and not left in the skills folder,
# where Claude Code would load it twice).
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$url    = 'https://github.com/yudhvirc/product-video-studio/releases/latest/download/product-video-studio.zip'
$skills = Join-Path $env:USERPROFILE '.claude\skills'
$dest   = Join-Path $skills 'product-video-studio'
$zip    = Join-Path $env:TEMP 'product-video-studio.zip'

New-Item -ItemType Directory -Force -Path $skills | Out-Null
Write-Host "Downloading $url ..."
Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing

if (Test-Path $dest) {
  $old = Join-Path $env:TEMP ('product-video-studio.old-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
  Move-Item -Path $dest -Destination $old
  Write-Host "Previous copy moved to $old"
}
Expand-Archive -Path $zip -DestinationPath $skills -Force
Remove-Item $zip

$manifest = Join-Path $dest '.claude-plugin\plugin.json'
if (-not (Test-Path $manifest)) { throw "Install failed: $manifest not found" }
$version = (Get-Content $manifest -Raw | ConvertFrom-Json).version
Write-Host "Installed product-video-studio $version to $dest"
Write-Host "Restart Claude Code to load it."
