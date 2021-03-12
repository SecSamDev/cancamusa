# Cancamusa 
> **Laboratorio de Carton-Piedra**

A Deception Platform

## Configuration
The cancamusa configuration is stored by default in `~/.cancamusa/preferences.json` and can be changed using the ENV_VAR **CANCAMUSA_HOME**

## How to use it

Set cancamusa command as a bash alias:
```
alias cancamusa='python3 ~/Workspace/cancamusa/cancamusa.py'
```

Required wimlib to register WindowsImages:
```
apt-get install wimtools
```

Inside an empty directory type `cancamusa`:
```
test1@Test1:~/cancamusa-labs/test2$ cancamusa
Not a valid cancamusa project
? No project found in the current path. Want to create a new Cancamusa project?  Yes
? Name of the project  test2
? Description of the project  Malware laboratory
? Configure a SIEM to send Windows Logs?  No
? Install Sysmon in each host?  No
? Select a project property:  
  > Description
  > Edit hosts
  > Sysmon
  > Elasticsearch
  > Logstash
  > Account Generator
  > Winlogbeat
  > Build
  > Deploy
  > Exit
```
This interactive menu will help you configure a full windows platform.

#### Edit hosts
This will give you power to cistomize each host in your new network:
```
? Select a project property:  Edit hosts
? Host edition mode Add host
? Editing host: Windows
  > Name
  > Disks
  > Bios
  > Accounts
  > Network interfaces
  > Back
  > Cancel
```
The name option will edit the hostname, "Disks" for adding disks, "Bios" for customizing the bios of the machine, when building the project, this will generate a .bin file of a modified version of SeaBIOS; "Accounts" for adding/editing accounts, "Network interfaces" for adding/editing new network interfaces and customize its address.
```
? Select a project property:  Edit hosts
? Host edition mode  Add host
? Editing host: Windows  Name
? Edit Hostname   Windows123
? Editing host: Windows123  Disks
? Modify disks  Add
? Select device ID  C
? Volume name  TestDiskWindows123
? Disk Size.  512G
? Editing host: Windows123  Cancel
? Host edition mode  Back
? Select a project property:  Exit
```

Now editing the bios version:
```
? Editing host: Windows123  Bios
? Edit: caption  BIOS Date: 05/30/14 21:22:47 Ver: 04.06.05
? Edit: description  BIOS Date: 05/30/14 21:22:47 Ver: 04.06.05
? Edit: embedded_controller_major_version  255
? Edit: embedded_controller_minor_version  255
? Edit: manufacturer  American Megatrends Inc.
? Edit: name  BIOS Date: 05/30/14 21:22:47 Ver: 04.06.05
? Edit: ps_computer_name  Windows123
? Edit: release_date  20140530000000.000000+000
? Edit: smbios_bios_version  F5
? Edit: smbios_major_version  2
? Edit: smbios_minor_version  7
? Edit: software_element_id  BIOS Date: 05/30/14 21:22:47 Ver: 04.06.05
? Edit: software_element_state  3
? Edit: system_bios_major_version  4
? Edit: system_bios_minor_version  6
? Edit: version  ALASKA - 1072009
```

The network interfaces selecting a "Random device", we can search for a custom vendor (See mac-vendor.txt):
```
? Editing host: Windows123  Network interfaces
? Modify interfaces  Add
? Network edition mode  Random device
? Edit: description  KARDIOS SYSTEMS CORP.
? Edit: dns_domain  
? Edit: dns_host_name  
? Edit: index  0
? Edit: interface_index  0
? Edit IpAddress  ['192.168.0.1']
? Edit: mac_address  00:20:77:97:5d:31
? Edit: setting_id  {49f6db5f-228b-42db-a89a-31a78b2d6eb7}
```


## TODO:
- Proxmox template creation with all scripts and drivers bundled in a ISO mounted in a CD/DVD device.
- Build custom network VirtIO drivers: https://github.com/virtio-win/kvm-guest-drivers-windows/wiki/Building-the-drivers


