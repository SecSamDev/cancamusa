$box = Get-ItemProperty -Path HKLM:SYSTEM\CurrentControlSet\Control\ComputerName\ComputerName -Name "ComputerName"
$box = $box.ComputerName.ToString().ToLower()

param (
    [String] $rol,
    [string] $scripts = "C:\sysinternals\scripts",
    [String] $ip,
    [String] $domain_ip,
    [String] $domain = "windomain.local",
    [String] $username = "cancamusa",
    [String] $password = "cancamusa",
    [String] $dns1 = "8.8.8.8",
    [String] $dns2 = "8.8.4.4"
)
if (!(Test-Path 'c:\Program Files\sysinternals\bginfo.exe')) {
    Write-Host 'Install bginfo'
    . c:\vagrant\scripts\install-bginfo.ps1
}


if ((gwmi win32_computersystem).partofdomain -eq $false) {

    Write-Host -fore red "Ooops, workgroup!"

    if ($rol -eq "dc"){
        $script = "$scripts\create-domain.ps1 -ip $ip -domain $domain -password $password -dns1 $dns1 -dns2 $dns2"
        . $script
    } else {
        # ALL must join domain
        $script = "$scripts\join-domain.ps1 -ip $ip -server $domain_ip -username $username -password $password -domain $domain"
        . $script
        if ($rol -eq "adfs"){

        }
    }

    Write-Host -fore red 'Hint: vagrant reload' $box '--provision'

} else {
    Write-Host -fore green "I am domain joined!"

    Write-Host 'Provisioning after joining domain'

    $script = "$scripts\provision-$box.ps1"
    . $script
}