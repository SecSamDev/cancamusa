$current_script = Split-Path $MyInvocation.MyCommand.Path -Parent
Copy-Item -Path "$current_script\profile.ps1" -Destination $profile -Force