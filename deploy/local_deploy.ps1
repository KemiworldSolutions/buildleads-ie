# Local deployment helper — run this on your local machine.
# Transfers the .env file to the VPS and kicks off remote setup.
#
# Usage:
#   .\deploy\local_deploy.ps1 -User Administrator
#   .\deploy\local_deploy.ps1 -User Administrator -EnvFile E:\Work\OPENCLAW\.env

param(
    [Parameter(Mandatory=$true)]
    [string]$User,

    [string]$Host     = "ssh.kwmarketslab.com",
    [string]$KeyFile  = "$env:USERPROFILE\.ssh\vps_id_ed25519",
    [string]$EnvFile  = "E:\Work\OPENCLAW\.env",
    [string]$DeployDir = "C:\BuildLeads"
)

$SshOpts = "-i `"$KeyFile`" -o ProxyCommand=`"cloudflared access ssh --hostname $Host`" -o StrictHostKeyChecking=no"
$Remote  = "$User@$Host"

function Invoke-Remote {
    param([string]$Cmd)
    $full = "ssh $SshOpts $Remote `"$Cmd`""
    Write-Host "  > $Cmd"
    Invoke-Expression $full
}

Write-Host "=== BuildLeads Remote Deployment ===" -ForegroundColor Cyan
Write-Host "Target: $Remote"
Write-Host ""

# 1. Test connection
Write-Host "[1/4] Testing SSH connection..."
Invoke-Remote "echo Connected as %USERNAME%"

# 2. Copy .env to VPS
Write-Host ""
Write-Host "[2/4] Transferring .env to VPS..."
$scpCmd = "scp $SshOpts `"$EnvFile`" `"${Remote}:$DeployDir\.env`""
Write-Host "  > (scp .env)"
Invoke-Expression $scpCmd

# 3. Run setup script on VPS
Write-Host ""
Write-Host "[3/4] Running vps_setup.ps1 on VPS..."
Invoke-Remote "powershell -ExecutionPolicy Bypass -File $DeployDir\deploy\vps_setup.ps1"

# 4. Register scheduled tasks
Write-Host ""
Write-Host "[4/4] Registering scheduled tasks..."
Invoke-Remote "powershell -ExecutionPolicy Bypass -File $DeployDir\deploy\register_task.ps1"

Write-Host ""
Write-Host "=== Deployment complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Test the pipeline manually:"
Write-Host "  ssh $SshOpts $Remote"
Write-Host "  cd C:\BuildLeads"
Write-Host "  .\.venv\Scripts\python.exe -m src.pipeline --limit 5"
