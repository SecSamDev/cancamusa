param ([String] $ip, [String] $dns)

$subnet = $ip -replace "\.\d+$", ""

$name = (Get-NetIPAddress -AddressFamily IPv4 `
   | Where-Object -FilterScript { ($_.IPAddress).StartsWith($subnet) } `
   ).InterfaceAlias

if (!$name) {
  $name = (Get-NetIPAddress -AddressFamily IPv4 `
     | Where-Object -FilterScript { ($_.IPAddress).StartsWith("169.254.") } `
     ).InterfaceAlias
}

if ($name) {
  Write-Host "Set IP address to $ip of interface $name"
  & netsh.exe int ip set address "$name" static $ip 255.255.255.0 "$subnet.1"

  if ($dns) {
    Write-Host "Set DNS server address to $dns of interface $name"
    & netsh.exe interface ipv4 add dnsserver "$name" address=$dns index=1
  }
} else {
  Write-Error "Could not find a interface with subnet $subnet.xx"
}