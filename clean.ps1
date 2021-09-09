#!/usr/bin/env pwsh

$component = Get-Content -Path "component.json" | ConvertFrom-Json
$buildImage="$($component.registry)/$($component.name):$($component.version)-$($component.build)-build"
$docsImage="$($component.registry)/$($component.name):$($component.version)-$($component.build)-docs"
$testImage="$($component.registry)/$($component.name):$($component.version)-$($component.build)-test"

# Clean up build directories
if (Test-Path "dist") {
    Remove-Item -Recurse -Force -Path "dist"
}

# Remove docker images
docker rmi $buildImage --force
docker rmi $docsImage --force
docker rmi $testImage --force
docker image prune --force
docker rmi -f $(docker images -f "dangling=true" -q) # remove build container if build fails

# Remove existed containers
$exitedContainers = docker ps -a | Select-String -Pattern "Exit"
foreach($c in $exitedContainers) { docker rm $c.ToString().Split(" ")[0] }

# Remove unused volumes
#docker volume rm -f $(docker volume ls -f "dangling=true")

# remove cash and temp files
Get-ChildItem -Path "." -Include "cache" -Recurse | Remove-Item -Recurse -Force
Get-ChildItem -Path "." -Include "dist" -Recurse | Remove-Item -Recurse -Force
Get-ChildItem -Path "." -Include "$($component.name.replace('-', '_')).egg-info" -Recurse | Remove-Item -Recurse -Force
Get-ChildItem -Path "." -Include "$($component.name.replace('-', '_'))/*.pyc" -Recurse | Remove-Item -Force
Get-ChildItem -Path "." -Include "$($component.name.replace('-', '_'))/**/*.pyc" -Recurse | Remove-Item -Force
Get-ChildItem -Path "." -Include "$($component.name.replace('-', '_'))/__pycache__" -Recurse | Remove-Item -Force
Get-ChildItem -Path "." -Include "test/__pycache__" -Recurse | Remove-Item -Recurse -Force
Get-ChildItem -Path "." -Include "test/**/__pycache__" -Recurse | Remove-Item -Recurse -Force
Get-ChildItem -Path "." -Include "test/.pytest_cache" -Recurse | Remove-Item -Recurse -Force
Get-ChildItem -Path "." -Include "test/**/.pytest_cache" -Recurse | Remove-Item -Recurse -Force

