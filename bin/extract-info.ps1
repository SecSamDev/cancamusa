# Almacenar todo en la carpeta hostname
$hostname = hostname
mkdir $hostname
$Usuario = [Environment]::UserName
# Configuracion de red
Get-WmiObject -Class Win32_NetworkAdapterConfiguration | Select-Object Description, SettingID, MACAddress, DNSDomain, DNSHostName, Index, InterfaceIndex, IPAddress | ConvertTo-Json | Out-File -Encoding UTF8 $hostname'\net.json'
# Discos instalados
Get-WmiObject -Class Win32_LogicalDisk | Select-Object DeviceID, DriveType, FreeSpace, Size, VolumeName | ConvertTo-Json | Out-File -Encoding UTF8 $hostname'\disk.json'
# Cuentas de usuario en el equipo, tanto locales como de dominio
Get-WmiObject -ComputerName $hostname -Class Win32_UserAccount | Select-Object LocalAccount,AccountType,Name, PSComputerName, Description,SID, Lockout, PasswordChangeable, PasswordExpires, PasswordRequired  | ConvertTo-Json | Out-File -Encoding UTF8 $hostname'\accounts.json'
# Estructura de directorios de l carpeta home del usuario
tree $HOME /f > $hostname/$Usuario'-tree.log'
# Información de la BIOS
Get-WmiObject Win32_Bios | ConvertTo-Json | Out-File -Encoding UTF8 $hostname/'bios.json'
[System.Environment]::OSVersion.Version | ConvertTo-JSON | Out-File -Encoding UTF8 $hostname/'version.json'
# Información del antivirus
Get-WmiObject -Namespace "root\SecurityCenter2" -Query "Select * From  AntiVirusProduct" | ConvertTo-Json | Out-File -Encoding UTF8 $hostname'\av.json'
# Programas instalados
Get-ItemProperty HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\* | Select-Object DisplayName, DisplayVersion, Publisher, InstallDate | ConvertTo-Json | Out-File -Encoding UTF8 $hostname'\programs.json'
# Roles instalados 
try{Get-WindowsFeature | Where-Object {$_.InstallState -eq 'Installed'} | Select-Object DisplayName, Name | ConvertTo-Json | Out-File -Encoding UTF8 $hostname'\roles.json'}
catch { "An error occurred." }

# CPU
Get-WmiObject -Class Win32_Processor | Select-Object -Property Name, Number* | ConvertTo-Json | Out-File -Encoding UTF8 $hostname'\cpu.json'
# RAM
Get-WmiObject win32_physicalmemory | Select-Object Manufacturer,Banklabel,Configuredclockspeed,Devicelocator,Capacity,Serialnumber | ConvertTo-Json | Out-File -Encoding UTF8 $hostname'\ram.json'

# Directorios sobre Program Files

$pf64 = Get-ChildItem 'C:\Program Files'
[System.Collections.ArrayList]$program_list = @()

foreach($company in $pf64){
    $program_names = Get-ChildItem 'C:\Program Files\'$company'\'
    if($program_names.Count -gt 4) {
        # Program files, not a product folder
        $prog_data = new-object psobject
        Add-Member -InputObject $prog_data -MemberType NoteProperty -Name company -Value $company.Name
        Add-Member -InputObject $prog_data -MemberType NoteProperty -Name program_name -Value $company.Name
        $a = $program_list.Add($prog_data)
    }else{
        foreach($name in $program_names){
        $test_path = 'C:\Program Files\' + $company + '\' + $name
            if((Get-Item $test_path) -is [System.IO.DirectoryInfo]){
                $prog_data = new-object psobject
                Add-Member -InputObject $prog_data -MemberType NoteProperty -Name company -Value $company.Name
                Add-Member -InputObject $prog_data -MemberType NoteProperty -Name program_name -Value $name.Name
                $a =$program_list.Add($prog_data)
            }
        
        }
    }
}
$program_list | ConvertTo-Json | Out-File -Encoding UTF8 $hostname'\Pfx64.json'

$pf32 = Get-ChildItem 'C:\Program Files (x86)'
[System.Collections.ArrayList]$program_list = @()

foreach($company in $pf32){
    $program_names = Get-ChildItem 'C:\Program Files (x86)\'$company'\'
    if($program_names.Count -gt 4) {
        # Program files, not a product folder
        $prog_data = new-object psobject
        Add-Member -InputObject $prog_data -MemberType NoteProperty -Name company -Value $company.Name
        Add-Member -InputObject $prog_data -MemberType NoteProperty -Name program_name -Value $company.Name
        $a = $program_list.Add($prog_data)
    }else{
        foreach($name in $program_names){
        $test_path = 'C:\Program Files (x86)\' + $company + '\' + $name
            if((Get-Item $test_path) -is [System.IO.DirectoryInfo]){
                $prog_data = new-object psobject
                Add-Member -InputObject $prog_data -MemberType NoteProperty -Name company -Value $company.Name
                Add-Member -InputObject $prog_data -MemberType NoteProperty -Name program_name -Value $name.Name
                $a =$program_list.Add($prog_data)
            }
        
        }
    }
}
$program_list | ConvertTo-Json | Out-File -Encoding UTF8 $hostname'\Pfx32.json'
