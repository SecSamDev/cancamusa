Remove-Item -Path Alias:\ls
function ls([switch] $lrt, [switch] $la) {
  if ( $lrt.IsPresent) {
    Get-ChildItem | Sort-Object LastWriteTime
  } elseif ($la.IsPresent){
    Get-ChildItem | Sort-Object LastWriteTime
  } else {
    Get-ChildItem $args
  }
}
function uptime {
    Get-WmiObject win32_operatingsystem | select csname, @{LABEL='LastBootUpTime'; EXPRESSION={$_.ConverttoDateTime($_.lastbootuptime)}}
}
function reload-profile {
    & $profile
}
function lsusb {
    gwmi Win32_USBControllerDevice
}
function find-file($name) {
    ls -recurse -filter "*${name}*" -ErrorAction SilentlyContinue | foreach {
        $place_path = $_.directory
        echo "${place_path}\${_}"
    }
}
function unzip ($file) {
    $dirname = (Get-Item $file).Basename
    echo("Extracting", $file, "to", $dirname)
    New-Item -Force -ItemType directory -Path $dirname
    expand-archive $file -OutputPath $dirname -ShowProgress
}
function grep($regex, $dir) {
    if ( $dir ) {
        ls $dir | select-string $regex
        return
    }
    $input | select-string $regex
}
function touch($file) {
    "" | Out-File $file -Encoding ASCII
}
function df {
    get-volume
}
function sed($file, $find, $replace){
    (Get-Content $file).replace("$find", $replace) | Set-Content $file
}
function which($name) {
    Get-Command $name | Select-Object -ExpandProperty Definition
}
function export($name, $value) {
    set-item -force -path "env:$name" -value $value;
}
function pkill($name) {
    ps $name -ErrorAction SilentlyContinue | kill
}
function pgrep($name) {
    ps $name
}
function ip {
    Get-NetIPAddress | Select-Object InterfaceAlias,IPAddress,PrefixOrigin, ValidLifetime
}
function nslookup($dom) {
    Resolve-DnsName $dom
}
Remove-Item -Path Alias:\wget
function wget($url) {
    Invoke-WebRequest -Uri $url -OutFile $url.split("/")[-1]
}