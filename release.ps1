#!/usr/bin/env pwsh

Set-StrictMode -Version latest
$ErrorActionPreference = "Stop"

# Get component data
$component = Get-Content -Path "component.json" | ConvertFrom-Json

# Create pypirc if not exists
if (!(Test-Path "~/.pypirc")) {
    $pypircContent = @"
[distutils]
index-servers=
    testpypi
    pypi

[testpypi]
repository = https://test.pypi.org/legacy/
username = $($env:PYPI_USER)
password = $($env:PYPI_PASS)

[pypi]
repository = https://upload.pypi.org/legacy/
username = $($env:PYPI_USER)
password = $($env:PYPI_PASS)
"@

    Set-Content -Path "~/.pypirc" -Value $pypircContent
}

# Release package
Write-Host "Pushing package to pipy"
python setup.py sdist
python -m twine upload --skip-existing dist/*

if ($LastExitCode -ne 0) {
    Write-Error "Release failed. Watch logs above."
}
