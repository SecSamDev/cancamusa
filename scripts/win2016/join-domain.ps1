param (
    [string][AllowEmptyString()]$net,
    [string]$server = "192.168.1.253",
    [string]$username "cancamusa",
    [string]$password = "cancamusa"
    [string]$domain = "windomain.local"
)
Write-Host 'Entrar en el dominio'
if (!$net){
    $net = $server -replace "\.\d+$", ""
}
Start-Sleep -m 2000

Write-Host "EL DNS debe ser el controlador de dominio"
$adapters = Get-WmiObject Win32_NetworkAdapterConfiguration | Where-Object {$_.IPAddress -match $net}
$adapters | ForEach-Object {$_.SetDNSServerSearchOrder($server)}

Start-Sleep -m 2000

Write-Host "Unirse al dominio"

$user = "$domain\$username"
$pass = ConvertTo-SecureString $password -AsPlainText -Force
$DomainCred = New-Object System.Management.Automation.PSCredential $user, $pass
Add-Computer -DomainName $domain -credential $DomainCred -PassThru

Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" -Name AutoAdminLogon -Value 1
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" -Name DefaultUserName -Value $username
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" -Name DefaultPassword -Value $password
###  Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" -Name DefaultDomainName -Value "WINDOMAIN"