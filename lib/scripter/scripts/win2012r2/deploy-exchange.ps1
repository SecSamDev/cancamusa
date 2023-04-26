Install-WindowsFeature RSAT-Clustering-CmdInterface, NET-Framework-45-Features, RPC-over-HTTP-proxy, RSAT-Clustering, RSAT-Clustering-CmdInterface, RSAT-Clustering-Mgmt, RSAT-Clustering-PowerShell, Web-Mgmt-Console, WAS-Process-Model, Web-Asp-Net45, Web-Basic-Auth, Web-Client-Auth, Web-Digest-Auth, Web-Dir-Browsing, Web-Dyn-Compression, Web-Http-Errors, Web-Http-Logging, Web-Http-Redirect, Web-Http-Tracing, Web-ISAPI-Ext, Web-ISAPI-Filter, Web-Lgcy-Mgmt-Console, Web-Metabase, Web-Mgmt-Console, Web-Mgmt-Service, Web-Net-Ext45, Web-Request-Monitor, Web-Server, Web-Stat-Compression, Web-Static-Content, Web-Windows-Auth, Web-WMI, Windows-Identity-Foundation, RSAT-ADDS



Import-Module BitsTransfer
Start-BitsTransfer -Source https://download.microsoft.com/download/2/C/4/2C47A5C1-A1F3-4843-B9FE-84C0032C61EC/UcmaRuntimeSetup.exe -Destination ./UcmaRuntimeSetup.exe

setup.exe /PrepareSchema /IAcceptExchangeServerLicenseTerms

Setup.exe /PrepareAD /OrganizationName: /IAcceptExchangeServerLicenseTerms

Setup.exe /PrepareAD /OrganizationName: /IAcceptExchangeServerLicenseTerms

Setup.exe /mode:Install /role:Mailbox /OrganizationName: /IAcceptExchangeServerLicenseTerms