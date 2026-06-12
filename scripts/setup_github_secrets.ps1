param(
  [string]$Repo = "cedriceckert85-wq/bots"
)

$ErrorActionPreference = "Stop"

function Read-PlainSecret {
  param([string]$Name)

  $secure = Read-Host "Paste value for $Name" -AsSecureString
  $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try {
    return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
  }
  finally {
    if ($bstr -ne [IntPtr]::Zero) {
      [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
  }
}

function Set-GitHubSecret {
  param([string]$Name)

  $value = Read-PlainSecret -Name $Name
  if ([string]::IsNullOrWhiteSpace($value)) {
    Write-Host "Skipped $Name (empty)."
    return
  }

  try {
    gh secret set $Name --repo $Repo --body $value
    if ($LASTEXITCODE -ne 0) {
      throw "gh secret set failed for $Name"
    }
    Write-Host "Set $Name"
  }
  finally {
    $value = $null
  }
}

gh auth status | Out-Host

$names = @(
  "ALPACA_SOLID_KEY",
  "ALPACA_SOLID_SECRET",
  "ALPACA_RISK_KEY",
  "ALPACA_RISK_SECRET",
  "ALPACA_CODEX_KEY",
  "ALPACA_CODEX_SECRET",
  "ALPACA_DAYTRADER_KEY",
  "ALPACA_DAYTRADER_SECRET"
)

foreach ($name in $names) {
  Set-GitHubSecret -Name $name
}
