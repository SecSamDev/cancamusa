$open_ssh_name = Get-WindowsCapability -Online | Where-Object Name -Like 'OpenSSH.Server*'
$open_ssh_name = $open_ssh_name[0].Name

Add-WindowsCapability -Online -Name $open_ssh_name

# Copy Authorized_keys
if (Test-Path -Path C:\ini\authorized_keys -PathType Leaf) {
    New-Item -ItemType Directory -Path "$($Env:programdata)\ssh" 2>&1 | Out-Null
    New-Item -ItemType Directory -Path "~\.ssh" 2>&1 | Out-Null

    Copy-Item C:\ini\authorized_keys -Destination "$($Env:programdata)\ssh\administrators_authorized_keys"
    Copy-Item C:\ini\authorized_keys -Destination "~\.ssh\authorized_keys"
}
icacls C:\ProgramData\ssh /remove:g *S-1-5-11


Start-Service sshd

Set-Service -Name sshd -StartupType 'Automatic'
# Confirm the Firewall rule is configured. It should be created automatically by setup. Run the following to verify
if (!(Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue | Select-Object Name, Enabled)) {
    Write-Output "Firewall Rule 'OpenSSH-Server-In-TCP' does not exist, creating it..."
    New-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -DisplayName 'OpenSSH Server (sshd)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
} else {
    Write-Output "Firewall rule 'OpenSSH-Server-In-TCP' has been created and exists."
}
