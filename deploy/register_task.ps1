# Register BuildLeads weekly pipeline as a Windows Scheduled Task
# Run once on the VPS after setup is complete.
# Requires: Administrator privileges

$DeployDir = "C:\BuildLeads"
$PythonExe = "$DeployDir\.venv\Scripts\python.exe"
$LogDir    = "$DeployDir\logs"

# Ensure log dir exists
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# --- Task 1: Weekly pipeline (scrape + extract + digest) ---
# Every Monday at 06:30 (VPS local time — adjust if VPS is not in Dublin/UTC+1)

$pipelineAction = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"cd /d $DeployDir && $PythonExe -m src.pipeline >> $LogDir\pipeline.log 2>&1`""

$pipelineTrigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Monday `
    -At "06:30AM"

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

Register-ScheduledTask `
    -TaskName "BuildLeads_Pipeline" `
    -TaskPath "\BuildLeads\" `
    -Action $pipelineAction `
    -Trigger $pipelineTrigger `
    -Settings $settings `
    -RunLevel Highest `
    -Force

Write-Host "Registered: \BuildLeads\BuildLeads_Pipeline (Mondays 06:30)"

# --- Task 2: Deliver digest to subscribers (30 min after pipeline) ---

$deliverAction = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"cd /d $DeployDir && $PythonExe -m src.deliver_subscribers >> $LogDir\deliver.log 2>&1`""

$deliverTrigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Monday `
    -At "07:00AM"

Register-ScheduledTask `
    -TaskName "BuildLeads_Deliver" `
    -TaskPath "\BuildLeads\" `
    -Action $deliverAction `
    -Trigger $deliverTrigger `
    -Settings $settings `
    -RunLevel Highest `
    -Force

Write-Host "Registered: \BuildLeads\BuildLeads_Deliver (Mondays 07:00)"
Write-Host ""
Write-Host "View tasks: Task Scheduler → Task Scheduler Library → BuildLeads"
Write-Host "Test now:   Start-ScheduledTask -TaskPath '\BuildLeads\' -TaskName 'BuildLeads_Pipeline'"
