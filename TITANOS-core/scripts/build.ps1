$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$LogPath = Join-Path $ProjectRoot "BUILD_LOG.md"
$Stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
$Status = "PASS"
$Details = New-Object System.Collections.Generic.List[string]

Push-Location $ProjectRoot
try {
    python -m compileall titanos | Out-String | ForEach-Object {
        if ($_.Trim()) { $Details.Add($_.Trim()) }
    }

    python -m titanos --sources | Out-String | ForEach-Object {
        if ($_.Trim()) { $Details.Add($_.Trim()) }
    }

    python -m titanos --providers | Out-String | ForEach-Object {
        if ($_.Trim()) { $Details.Add($_.Trim()) }
    }

    python -m unittest discover -s tests | Out-String | ForEach-Object {
        if ($_.Trim()) { $Details.Add($_.Trim()) }
    }

    $UiFiles = @("ui\index.html", "ui\styles.css", "ui\main.js", "ui\api.js", "ui\ui-components.js")
    foreach ($UiFile in $UiFiles) {
        if (-not (Test-Path (Join-Path $ProjectRoot $UiFile))) {
            throw "Missing UI file: $UiFile"
        }
        $Details.Add("UI present: $UiFile")
    }
}
catch {
    $Status = "FAIL"
    $Details.Add($_.Exception.Message)
    throw
}
finally {
    Pop-Location

    Add-Content -Path $LogPath -Value ""
    Add-Content -Path $LogPath -Value "## $Stamp - $Status"
    Add-Content -Path $LogPath -Value ""
    Add-Content -Path $LogPath -Value "Checks:"
    Add-Content -Path $LogPath -Value "- python -m compileall titanos"
    Add-Content -Path $LogPath -Value "- python -m titanos --sources"
    Add-Content -Path $LogPath -Value "- python -m titanos --providers"
    Add-Content -Path $LogPath -Value "- python -m unittest discover -s tests"
    Add-Content -Path $LogPath -Value "- ui/index.html, ui/styles.css, ui/main.js, ui/api.js, ui/ui-components.js present"
    Add-Content -Path $LogPath -Value ""
    Add-Content -Path $LogPath -Value "Output:"
    foreach ($Line in $Details) {
        Add-Content -Path $LogPath -Value "- $Line"
    }
}
