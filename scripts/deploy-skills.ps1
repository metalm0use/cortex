[CmdletBinding()]
param(
    [ValidateSet("auto", "codex", "claude", "gemini", "all")]
    [string]$Agent = "auto",

    [string]$Target,

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Get-FrontmatterValue {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Key
    )

    $lines = Get-Content -LiteralPath $Path
    if ($lines.Count -eq 0 -or $lines[0] -ne "---") {
        return $null
    }

    for ($i = 1; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        if ($line -eq "---") {
            break
        }
        if ($line.StartsWith("${Key}:")) {
            $value = $line.Substring($Key.Length + 1).Trim()
            return $value.Trim('"').Trim("'")
        }
    }

    return $null
}

function ConvertTo-CortexSkillName {
    param([Parameter(Mandatory = $true)][string]$SkillId)

    $name = "cortex-$SkillId".ToLowerInvariant()
    $name = $name -replace "[^a-z0-9]+", "-"
    return $name.Trim("-")
}

function ConvertTo-YamlDoubleQuoted {
    param([Parameter(Mandatory = $true)][string]$Value)

    return ($Value -replace "\\", "\\" -replace '"', '\"')
}

function Get-AgentTargetRoot {
    param([Parameter(Mandatory = $true)][string]$Name)

    switch ($Name) {
        "codex" {
            $homeRoot = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
            return Join-Path $homeRoot "skills"
        }
        "claude" {
            $homeRoot = if ($env:CLAUDE_HOME) { $env:CLAUDE_HOME } else { Join-Path $HOME ".claude" }
            return Join-Path $homeRoot "skills"
        }
        "gemini" {
            $homeRoot = if ($env:GEMINI_HOME) { $env:GEMINI_HOME } else { Join-Path $HOME ".gemini" }
            return Join-Path $homeRoot "skills"
        }
    }
}

function Get-DetectedAgents {
    $found = @()
    if ($env:CODEX_HOME -or (Test-Path -LiteralPath (Join-Path $HOME ".codex"))) {
        $found += "codex"
    }
    if ($env:CLAUDE_HOME -or (Test-Path -LiteralPath (Join-Path $HOME ".claude"))) {
        $found += "claude"
    }
    if ($env:GEMINI_HOME -or (Test-Path -LiteralPath (Join-Path $HOME ".gemini"))) {
        $found += "gemini"
    }
    return $found
}

function Get-DeploymentTargets {
    if ($Target) {
        return @([pscustomobject]@{
            Agent = $Agent
            Root = $Target
        })
    }

    if ($Agent -eq "auto") {
        return @(Get-DetectedAgents | ForEach-Object {
            [pscustomobject]@{
                Agent = $_
                Root = Get-AgentTargetRoot $_
            }
        })
    }

    if ($Agent -eq "all") {
        return @("codex", "claude", "gemini" | ForEach-Object {
            [pscustomobject]@{
                Agent = $_
                Root = Get-AgentTargetRoot $_
            }
        })
    }

    return @([pscustomobject]@{
        Agent = $Agent
        Root = Get-AgentTargetRoot $Agent
    })
}

function Write-CortexWrapper {
    param(
        [Parameter(Mandatory = $true)][string]$AgentName,
        [Parameter(Mandatory = $true)][string]$TargetRoot,
        [Parameter(Mandatory = $true)][string]$SourceFile,
        [Parameter(Mandatory = $true)][string]$VaultRoot
    )

    $skillId = Get-FrontmatterValue -Path $SourceFile -Key "skill_id"
    $summary = Get-FrontmatterValue -Path $SourceFile -Key "summary"
    $modelRole = Get-FrontmatterValue -Path $SourceFile -Key "model_role"
    $status = Get-FrontmatterValue -Path $SourceFile -Key "status"

    if (-not $skillId) {
        Write-Warning "Skipping $SourceFile because it has no skill_id."
        return
    }

    if (-not $modelRole) {
        $modelRole = "reference"
    }
    if (-not $status) {
        $status = "unknown"
    }

    $name = ConvertTo-CortexSkillName -SkillId $skillId
    $destination = Join-Path $TargetRoot $name
    $marker = Join-Path $destination ".cortex-managed"

    if ((Test-Path -LiteralPath $destination) -and -not (Test-Path -LiteralPath $marker)) {
        Write-Host "SKIP: $destination exists and is not Cortex-managed"
        return
    }

    Write-Host "DEPLOY: $AgentName $skillId -> $destination"
    if ($DryRun) {
        return
    }

    New-Item -ItemType Directory -Force -Path $destination | Out-Null

    @"
generated_by=cortex
vault_root=$VaultRoot
source=$SourceFile
agent=$AgentName
"@ | Set-Content -LiteralPath $marker -Encoding UTF8

    $description = ConvertTo-YamlDoubleQuoted -Value "Cortex skill $skillId. $summary Read the source vault file before acting; updates belong in the Cortex repo."
    $wrapper = @"
---
name: $name
description: "$description"
---

# Cortex: $skillId

This is a generated $AgentName wrapper for a Cortex vault skill.

Source of truth: ``$SourceFile``
Vault root: ``$VaultRoot``
Model role: ``$modelRole``
Status: ``$status``

Before using this skill, read the source file above. For orientation,
read ``$VaultRoot/skills/meta/index/SKILL.md``. After learning anything
vault-worthy, follow ``$VaultRoot/skills/meta/contributing/SKILL.md``.

Do not edit this generated wrapper directly. Update the source skill in
the Cortex repository, then redeploy wrappers with:

``````powershell
scripts/deploy-skills.ps1 -Agent $AgentName
``````
"@

    Set-Content -LiteralPath (Join-Path $destination "SKILL.md") -Value $wrapper -Encoding UTF8
}

$vaultRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$skillsRoot = Join-Path $vaultRoot "skills"
$targets = @(Get-DeploymentTargets)

if ($targets.Count -eq 0) {
    throw "No agent home detected. Use -Agent codex|claude|gemini or -Target <directory>."
}

$skillFiles = Get-ChildItem -LiteralPath $skillsRoot -Recurse -Filter "*.md" |
    Where-Object { $_.FullName -notmatch "\\scripts\\" } |
    Sort-Object FullName

foreach ($skillFile in $skillFiles) {
    foreach ($deploymentTarget in $targets) {
        Write-CortexWrapper `
            -AgentName $deploymentTarget.Agent `
            -TargetRoot $deploymentTarget.Root `
            -SourceFile $skillFile.FullName `
            -VaultRoot $vaultRoot
    }
}
