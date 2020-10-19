param (
    [string]$scripts = "C:\sysinternals\scripts"
)

Import-Module ActiveDirectory
NEW-ADOrganizationalUnit -name "IT-Services"
NEW-ADOrganizationalUnit -name "SupportGroups" -path "OU=IT-Services,DC=windomain,DC=local"
NEW-ADOrganizationalUnit -name "CostCenter" -path "OU=SupportGroups,OU=IT-Services,DC=windomain,DC=local"

NEW-ADOrganizationalUnit -name "Locations"
NEW-ADOrganizationalUnit -name "HeadQuarter" -path "OU=Locations,DC=windomain,DC=local"
NEW-ADOrganizationalUnit -name "Users" -path "OU=HeadQuarter,OU=Locations,DC=windomain,DC=local"

New-ADGroup -Name "SecurePrinting" -SamAccountName SecurePrinting -GroupCategory Security -GroupScope Global -DisplayName "Secure Printing Users" -Path "OU=SupportGroups,OU=IT-Services,DC=windomain,DC=local"
New-ADGroup -Name "CostCenter-123" -SamAccountName CostCenter-123 -GroupCategory Security -GroupScope Global -DisplayName "CostCenter 123 Users" -Path "OU=CostCenter,OU=SupportGroups,OU=IT-Services,DC=windomain,DC=local"
New-ADGroup -Name "CostCenter-125" -SamAccountName CostCenter-125 -GroupCategory Security -GroupScope Global -DisplayName "CostCenter 125 Users" -Path "OU=CostCenter,OU=SupportGroups,OU=IT-Services,DC=windomain,DC=local"


$ADUsers = Import-csv $scripts\users.csv

foreach ($User in $ADUsers){
  $Username     = $User.username
  $Password     = $User.password
  $Firstname    = $User.firstname
  $Lastname     = $User.lastname
  $Department   = $User.department
  $OU           = $User.ou

  #Check if the user account already exists in AD
  if (Get-ADUser -F {SamAccountName -eq $Username}){
    Write-Warning "A user account $Username has already exist in Active Directory."
  }else{
    New-ADUser `
      -SamAccountName $Username `
      -UserPrincipalName "$Username@yourdomain.com" `
      -Name "$Firstname $Lastname" `
      -GivenName $Firstname `
      -Surname $Lastname `
      -Enabled $True `
      -ChangePasswordAtLogon $True `
      -DisplayName "$Lastname, $Firstname" `
      -Department $Department `
      -Path $OU `
      -AccountPassword (convertto-securestring $Password -AsPlainText -Force)
  }
}