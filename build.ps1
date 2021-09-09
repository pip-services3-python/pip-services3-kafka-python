#!/usr/bin/env pwsh

Set-StrictMode -Version latest
$ErrorActionPreference = "Stop"

# Get component data and set necessary variables
$component = Get-Content -Path "component.json" | ConvertFrom-Json
$buildImage="$($component.registry)/$($component.name):$($component.version)-$($component.build)-build"
$container=$component.name

# Copy private keys to access git repo
if (-not (Test-Path -Path "docker/id_rsa")) {
    if ($env:GIT_PRIVATE_KEY -ne $null) {
        $decodedGitPrivateKey = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($env:GIT_PRIVATE_KEY))
        Set-Content -Path "docker/id_rsa" -Value $decodedGitPrivateKey
    } else {
        Copy-Item -Path "~/.ssh/id_rsa" -Destination "docker"
    }
}

# Build docker image
docker build -f docker/Dockerfile.build -t $buildImage .

# Create and destroy container
docker create --name $container $buildImage
docker rm $container