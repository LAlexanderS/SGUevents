param(
    [string[]]$MkdocsArgs
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Resolve-Path (Join-Path $root "..")
Set-Location $repo

$envFile = Join-Path $repo ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -match '^\s*#' -or $line -match '^\s*$') { return }
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*[:=]\s*(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            if ($value -match '\s+#') {
                $value = ($value -split '\s+#',2)[0].Trim()
            }
            if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
                if ($value.Length -ge 2) {
                    $value = $value.Substring(1, $value.Length - 2)
                }
            }
            [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

$pythonBin = $env:PYTHON_BIN
if (-not $pythonBin) {
    $venvPython = Join-Path $repo "venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        $pythonBin = $venvPython
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        $pythonBin = (Get-Command python).Source
    } else {
        throw "Не найден python. Установите его или укажите PYTHON_BIN."
    }
}

& $pythonBin -m mkdocs build -f mkdocs.yml -d static/docs @MkdocsArgs

