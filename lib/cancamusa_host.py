import os
import json
from PyInquirer import prompt
import bios_database
import re
import random
import codecs
from mac_vendors import get_mac_list, search_wildcard_vendor, random_mac_for_vendor
from cancamusa_common import random_guid
from rol_selector import AVAILABLE_ROLES, roles_from_extracted_info

from processors import list_processors

class InteractiveHostEditor:
    
    def edit_hosts(cancamusa):
        """Edit the hosts inside a CancamusaProject

        Args:
            cancamusa: Cancamusa project
        Returns:
            The edited cancamusa project
    """
        answers = prompt([{'type': 'list','name': 'host_option','message': 'Select an option', 'choices' : ['Import hosts', 'Edit host','Delete host','Create Host', 'Exit']}])

        if answers['option'] == 'Import hosts':
            answers = prompt([{'type': 'input','name': 'hosts_path','message': 'Where is the host information location?'}])
            try:
                hosts = read_host_files_in_path(answers['hosts_path'])
            except:
                print("Cannot read hosts import paths: " + answers['hosts_path'])
            for host in hosts:
                # Check if it does not alredy exists
                cancamusa.add_host(host)
            
    def change_bios(host_info):
        bios_list = list(map(lambda x: x['Name'] + " " + x['Manufacturer'], bios_database.BIOS_LIST))
        bios_list.insert(0,'Use built in bios')
        answers = prompt([{'type': 'list','name': 'host_option','message': 'Select a bios', 'choices' : bios_list}])
        pos = bios_list.index(answers['host_option'])
        if pos < 0:
            host_info.bios = None
        else:
            host_info.bios = HostInfoBios(bios_database.BIOS_LIST[pos])

def read_host_information(pth):
    return HostInfo.host_info_from_directory(pth)

def read_host_files_in_path(pth):
    if not os.path.isdir(pth):
        raise Exception("Invalid host info path: " + path)
    
    host_in_dir = os.listdir(pth)
    host_list = []
    for host_dir in host_in_dir:
        try:
            host_list.append(read_host_information(os.path.join(pth,host_dir)))
        except:
            print('Error reading host information for ' + host_dir)
    return host_list





"""
 Creates a clone of a real machine to use in a virtualized network of the corporation.
 The generated machine is a stuntmachine (stuntman) of the real machine.
 This script needs info extracted using "extract-info.ps1"
"""
class HostInfoBios:
    def __init__(self, bios):
        self.manufacturer = bios['Manufacturer']
        self.version = bios['Version']
        self.caption = bios['Caption']
        self.description = bios['Description']
        self.release_date = bios['ReleaseDate']
        self.name = bios['Name']
        self.software_element_id = bios['SoftwareElementID']
        self.software_element_state = bios['SoftwareElementState']
        self.system_bios_major_version = bios['SystemBiosMajorVersion']
        self.system_bios_minor_version = bios['SystemBiosMinorVersion']
        self.smbios_major_version = bios['SMBIOSMajorVersion']
        self.smbios_minor_version = bios['SMBIOSMinorVersion']
        self.embedded_controller_major_version = bios['EmbeddedControllerMajorVersion']
        self.embedded_controller_minor_version = bios['EmbeddedControllerMinorVersion']
        self.ps_computer_name = bios['PSComputerName']
        self.smbios_bios_version = bios['SMBIOSBIOSVersion']
    
    def __str__(self):
        return "Manufacturer {}. Name: {}, Version: {}.".format(self.manufacturer, self.name, self.version)

    def edit_interactive(self):
        property_names = list(map(lambda x: str(x),dir(self)))
        class_props =  list(map(lambda x: str(x),dir(HostInfoBios)))
        for element in class_props:
            property_names.pop(property_names.index(element))

        for prop in property_names:
            if prop.startswith("_"):
                continue
            answer = prompt([{'type': 'input','name': 'option','message': 'Edit: ' +str(prop), 'default' :str(getattr(self,prop))}])
            setattr(self,prop,answer['option'])
        return self

    def create_interactive():
        examples = ['Custom','Back'] + bios_database.BIOS_LIST
        answer = prompt([{'type': 'list','name': 'option','message': 'Select a bios: ' + self.ps_computer_name, 'choices' : examples}])
        if answer['option'] == 'Custom':
            bios = HostInfoBios(bios_database.BIOS_AMERICAN_MEGATREND_ALASKA_F5)
            bios.edit_interactive()
            return bios
        if answer['option'] == 'Back':
            return
        
    def to_json(self):
        return {
            'Manufacturer' : self.manufacturer,
            'Version' : self.version,
            'Caption' : self.caption,
            'Description' : self.description,
            'ReleaseDate' : self.release_date,
            'Name' : self.name,
            'SoftwareElementID' : self.software_element_id,
            'SoftwareElementState' : self.software_element_state,
            'SystemBiosMajorVersion' : self.system_bios_major_version,
            'SystemBiosMinorVersion' : self.system_bios_minor_version,
            'SMBIOSMajorVersion' : self.system_bios_minor_version,
            'SMBIOSMinorVersion' : self.system_bios_minor_version,
            'EmbeddedControllerMajorVersion' : self.embedded_controller_major_version,
            'EmbeddedControllerMinorVersion' : self.embedded_controller_minor_version,
            'PSComputerName' : self.ps_computer_name,
            'SMBIOSBIOSVersion': self.smbios_bios_version,
        }
    
    def from_json(obj):
        return HostInfoBios(obj)

class HostInfoPrograms:
    def __init__(self, display_name, display_version, publisher, install_date):
        self.display_name = display_name
        self.display_version = display_version
        self.publisher = publisher
        self.install_date = install_date
    
    def edit_interactive(self):
        # Don't know what to do here
        return self

    def to_json(self):
        return {
            'DisplayName' : self.display_name,
            'DisplayVersion' : self.display_version,
            'Publisher' : self.publisher,
            'InstallDate' : self.install_date
        }

    def from_json(obj):
        return HostInfoPrograms(obj['DisplayName'], obj['DisplayVersion'], obj['Publisher'],obj['InstallDate'])

class HostInfoRoles:
    def __init__(self, roles):
        self.roles = roles
    
    def edit_interactive(self):
        # Don't know what to do here
        return self

    def create_interactive():
        examples = [] + AVAILABLE_ROLES + ['Back']
        answer = prompt([{'type': 'list','name': 'option','message': 'Select a server role: ', 'choices' : examples}])
        answ = answer['option']
        if answ == 'Back':
            return
        else:
            return [{'name' : answ}]


    def to_json(self):
        toRet =  []
        for rol in self.roles:
            toRet.append({'name' : rol['name']})
        return toRet

    def from_json(roles):
        if len(roles) > 0 and 'DisplayName' in roles[0]:
            # Not processed
            role_list = roles_from_extracted_info(roles)
        else:
            return HostInfoRole(roles)


class HostInfoDisk:
    def __init__(self, device_id, volume_name, size, free_space):
        self.device_id = device_id[0] # Only letter
        self.volume_name = volume_name
        self.size = size
        self.free_space = free_space
    
    def __str__(self):
        return "{}: {} ({})".format(self.device_id, self.volume_name, size_numeric_to_textual(self.size))
    
    def edit_interactive(self):
        answer = prompt([{'type': 'input','name': 'option','message': 'Select device ID', 'default' : self.device_id}])
        if len(answer['option']) != 1:
            print("Drive letter must be 1 character long")
            return
        else:
            self.device_id = answer['option']
        answer = prompt([{'type': 'input','name': 'option','message': 'Volume name', 'default' : self.volume_name}])
        self.volume_name = answer['option']
        answer = prompt([{'type': 'input','name': 'option','message': 'Disk Size.', 'default' : size_numeric_to_textual(self.size)}])
        size = size_textual_to_numeric(answer['option'])
        self.size = size
        self.free_space = random_free_size(size)
        return self

    def create_interactive(last_leter="B"):
        disk = HostInfoDisk(next_letter(last_leter),"My PC",64098583552,20828822016)
        disk = disk.edit_interactive()
        return disk
    def to_json(self):
        return {
            'DeviceID' : self.device_id,
            'VolumeName' : self.volume_name,
            'Size' : self.size,
            'FreeSpace' : self.free_space
        }
    
    def from_json(obj):
        return HostInfoDisk(obj['DeviceID'], obj['VolumeName'], obj['Size'],obj['FreeSpace'])
        


class HostInfoNetwork:
    def __init__(self, net_object):
        if net_object:
            self.description = net_object['Description']
            self.setting_id = net_object['SettingID']
            self.mac_address = net_object['MACAddress']
            self.dns_domain = net_object['DNSDomain']
            self.dns_host_name = net_object['DNSHostName']
            self.index = int(net_object['Index'])
            self.interface_index = int(net_object['InterfaceIndex'])
            if net_object['IPAddress'] and isinstance(net_object['IPAddress'], list):
                self.ip_address = net_object['IPAddress']
            else:
                self.ip_address = []             
    def __str__(self):
        return "{}: {} ({}) [{}]".format(self.index, self.description, self.mac_address, ",".join(self.ip_address))

    def edit_interactive(self):
        property_names = list(map(lambda x: str(x),dir(self)))
        class_props =  list(map(lambda x: str(x),dir(HostInfoNetwork)))
        for element in class_props:
            property_names.pop(property_names.index(element))

        for prop in property_names:
            if prop.startswith("_"):
                continue
            if prop == 'ip_address':
                answer = prompt([{'type': 'input','name': 'option','message': 'Edit IpAddress', 'default' :str(getattr(self,prop))}])
                to_parse = answer['option'].strip()
                if to_parse.startswith("["):
                    to_parse = to_parse[1:]
                if to_parse.endswith("]"):
                    to_parse = to_parse[:-1]
                split = list(map(lambda x: x.replace("'",'').strip(),to_parse.split(',')))
                self.ip_address = split
                continue
            answer = prompt([{'type': 'input','name': 'option','message': 'Edit: ' +str(prop), 'default' :str(getattr(self,prop))}])
            setattr(self,prop,answer['option'])
        self.index = int(self.index)
        self.interface_index = int(self.interface_index)
        return self

    def create_interactive(last_index=-1):
        answer = prompt([{'type': 'list','name': 'option','message': 'Network edition mode', 'choices' : ['Random device', 'Search vendor','Basic']}])
        netwrk = None
        if answer['option'] == 'Random device':
            device = search_wildcard_vendor(get_mac_list(),'*')
            netwrk = HostInfoNetwork({
                'Description' : device['vendor'],
                'SettingID' : "{" + random_guid() + "}",
                'MACAddress' : random_mac_for_vendor(device['mac']),
                'DNSDomain' : '',
                'DNSHostName' : '',
                'Index' : int(last_index) + 1,
                'InterfaceIndex' : int(last_index) + 1,
                'IPAddress' : ["192.168.0.1"],
            })
        elif answer['option'] == 'Search vendor':
            while True:
                mac_list = get_mac_list()
                device = search_wildcard_vendor(mac_list,'*')
                answer = prompt([{'type': 'input','name': 'option','message': 'Search by vendor name'}])
                macs = []
                names = []
                name = answer['option'].lower()
                for vndr in mac_list:
                    if name in vndr['vendor'].lower():
                        macs.append(vndr['mac'])
                        names.append(vndr['vendor'])
                if len(names) == 0:
                    print("No vendor found with this name")
                    continue
                answer = prompt([{'type': 'list','name': 'option','message': 'Select a vendor', 'choices' : names}])
                pos = names.index(answer['option'])

                netwrk = HostInfoNetwork({
                    'Description' : names[pos],
                    'SettingID' :  "{" + random_guid() + "}",
                    'MACAddress' : random_mac_for_vendor(macs[pos]),
                    'DNSDomain' : '',
                    'DNSHostName' : '',
                    'Index' : int(last_index) + 1,
                    'InterfaceIndex' : int(last_index) + 1,
                    'IPAddress' : ["192.168.0.1"],
                })
                break
        elif answer['option'] == 'Basic':
            netwrk = HostInfoNetwork({
                'Description' : 'Killer E2200 Gigabit Ethernet Controller',
                'SettingID' :  "{" + random_guid() + "}",
                'MACAddress' : random_mac_for_vendor(search_wildcard_vendor(get_mac_list(),'FCAA14')['mac']),
                'DNSDomain' : '',
                'DNSHostName' : '',
                'Index' : int(last_index) + 1,
                'InterfaceIndex' : int(last_index) + 1,
                'IPAddress' : ["192.168.0.1"],
            })
        netwrk = netwrk.edit_interactive()
        return netwrk

    def to_json(self):
        return {
            'Description' : self.description,
            'SettingID' : self.setting_id,
            'MACAddress' : self.mac_address,
            'DNSDomain' : self.dns_domain,
            'DNSHostName' : self.dns_host_name,
            'Index' : int(self.index),
            'InterfaceIndex' : int(self.interface_index),
            'IPAddress' : self.ip_address,
        }
    def from_json(net_object):
        return HostInfoNetwork(net_object)

class HostInfoWindowsVersion:
    def __init__(self, major,minor,build,revision,major_revision,minor_revision):
        self.major = major
        self.minor = minor
        self.build = build
        self.revision = revision
        self.major_revision = major_revision
        self.minor_revision = minor_revision

    def __str__(self):
        return "{}.{} {} ({})".format(self.major, self.minor, self.build, self.revision)
    
    def edit_interactive(self):
        pass

    def to_json(self):
        return {
            'Major' : self.major,
            'Minor' : self.minor,
            'Build' : self.build,
            'Revision' : self.revision,
            'MajorRevision' : self.major_revision,
            'MinorRevision' : self.minor_revision
        }
    
    def from_json(version_file):
        return HostInfoWindowsVersion(version_file['Major'],version_file['Minor'],version_file['Build'],version_file['Revision'], version_file['MajorRevision'],version_file['MinorRevision'])


class HostInfoCpu:
    def __init__(self, name,cores,threads):
        self.name = name
        self.family = "Intel"
        self.cores = cores
        self.threads = threads
        self.processor_type = "Haswell"

    def __str__(self):
        return "{} {}/{}".format(self.name, self.cores, self.threads)
    
    def edit_interactive(self):
        answer = prompt([{'type': 'input','name': 'option','message': 'Select CPU name', 'default' : self.name}])
        self.name = answer['option']
        self.detect_cpu_family()
        answer = prompt([{'type': 'input','name': 'option','message': 'Cores:', 'default' : str(self.cores)}])
        self.cores = int(answer['option'])
        answer = prompt([{'type': 'input','name': 'option','message': 'Threads: ', 'default' : str(self.threads)}])
        self.threads = int(answer['option'])
        answer = prompt([{'type': 'list','name': 'option','message': 'Select a QEMU cpu type:', 'choices' :list_processors(self.family)}])
        self.processor_type = answer['option']
        return self

    def detect_cpu_family(self):
        if 'Intel' in self.name:
            self.family = "Intel"
        elif 'AMD' in self.name:
            self.family = "AMD"
        else:
            self.family = None


    def to_json(self):
        return {
            'Name' : self.name,
            'NumberOfCores' : self.cores,
            'NumberOfLogicalProcessors' : self.threads,
            'Family' : self.family,
            'CpuType' : self.processor_type
        }
    
    def from_json(version_file):

        return HostInfoCpu(version_file['Name'],version_file['NumberOfCores'],version_file['NumberOfLogicalProcessors'])


class HostInfoWindowsAccounts:
    def __init__(self, account):
        self.name = account['Name']
        self.local_account = account['LocalAccount']
        self.account_type = account['AccountType']
        self.ps_computer_name = account['PSComputerName']
        self.description = account['Description']
        self.sid = account['SID']
        self.lockout = account['Lockout']
        self.password_changeable = account['PasswordChangeable']
        self.password_expires = account['PasswordExpires']
        self.password_required = account['PasswordRequired']
    
    def edit_interactive(self):
        property_names = list(map(lambda x: str(x),dir(self)))
        class_props =  list(map(lambda x: str(x),dir(HostInfoWindowsAccounts)))
        for element in class_props:
            property_names.pop(property_names.index(element))

        for prop in property_names:
            if prop.startswith("_"):
                continue
            answer = prompt([{'type': 'input','name': 'option','message': 'Edit: ' +str(prop), 'default' :str(getattr(self,prop))}])
            setattr(self,prop,answer['option'])
        return self

    def __str__(self):
        return "{} : {}".format(self.name, self.description)

    def create_interactive(host_name="Windows"):
        disk = HostInfoWindowsAccounts({
            'Name' : 'Administrator',
            'LocalAccount' : True,
            'AccountType' : 512,
            'PSComputerName' : host_name,
            'Description' : "Cuenta integrada para el acceso como invitado al equipo o dominio",
            'SID' : 'S-1-5-21-2718119982-1426233563-2378531167-500',
            'Lockout' : False,
            'PasswordChangeable' : True,
            'PasswordExpires' : False,
            'PasswordRequired' : True
        })
        disk = disk.edit_interactive()
        return disk

    def to_json(self):
        return {
            'Name' : self.name,
            'LocalAccount' : self.local_account,
            'AccountType' : self.account_type,
            'PSComputerName' : self.ps_computer_name,
            'Description' : self.description,
            'SID' : self.sid,
            'Lockout' : self.lockout,
            'PasswordChangeable' : self.password_changeable,
            'PasswordExpires' : self.password_expires,
            'PasswordRequired' : self.password_required
        }
    def from_json(account):
        return HostInfoWindowsAccounts(account)







class HostInfo:
    def __init__(self,host_id=1000):
        self.host_id = host_id
        self.disks = []
        self.bios = HostInfoBios(bios_database.BIOS_AMERICAN_MEGATREND_ALASKA_F5)
        self.computer_name = "Windows"
        self.networks = []
        self.os = HostInfoWindowsVersion(10,0,0,0,0,0)
        self.accounts = []
        self.programs = []
        self.roles = []
        self.cpus = []
    
    def add_disk(self,disk):
        for dsk in self.disks:
            if dsk.device_id == disk.device_id:
                return
        self.disks.append(disk)

    def add_network(self,net):
        last_index = 0
        for nt in self.networks:
            if nt.index > last_index:
                last_index = nt.index + 1
        if net.index < last_index:
            net.index = last_index
        self.networks.append(net)

    def __str__(self):
        to_ret = "ComputerName: {}\n".format(self.computer_name)
        to_ret += "BIOS:\n\t{}\n".format(self.bios)
        to_ret +="Disks:\n"
        for disk in self.disks:
            to_ret += "\t{}\n".format(disk)
        to_ret +="Accounts:\n"
        for acc in self.accounts:
            to_ret += "\t{}\n".format(acc)
        to_ret +="Network Interfaces:\n"
        for nt in self.networks:
            to_ret += "\t{}\n".format(nt)
        to_ret +="CPUs:\n"
        for nt in self.cpus:
            to_ret += "\t{}\n".format(nt)
        return to_ret
    
    def to_json(self):
        to_ret = {
            'host_id' : self.host_id,
            'cpus' : []
        }
        to_ret['disks'] = []
        to_ret['accounts'] = []
        to_ret['networks'] = []
        for disk in self.disks:
            to_ret['disks'].append(disk.to_json())
        for acc in self.accounts:
            to_ret['accounts'].append(acc.to_json())
        for nt in self.networks:
            to_ret['networks'].append(nt.to_json())
        for cpu in self.cpus:
            to_ret['cpus'].append(cpu.to_json())
        to_ret['bios'] = self.bios.to_json()
        to_ret['roles'] = []
        to_ret["os"] = self.os.to_json()
        to_ret["computer_name"] = self.computer_name
        return to_ret

    def from_json(obj):
        host = HostInfo()
        for disk in obj['disks']:
            host.disks.append(HostInfoDisk.from_json(disk))
        for acc in obj['accounts']:
            acc2 = HostInfoWindowsAccounts.from_json(acc)
            acc2.ps_computer_name = obj["computer_name"]
            host.accounts.append(acc2)
        for nt in obj['networks']:
            host.networks.append(HostInfoNetwork.from_json(nt))
        if 'cpus' in obj:
            for cpu in obj['cpus']:
                host.cpus.append(HostInfoCpu.from_json(cpu))
        if len(host.cpus) == 0:
            host.cpus.append(HostInfoCpu("Intel(R) Xeon(R) CPU E5-2430L v2 @ 2.40GHz",6,12))
        host.bios = HostInfoBios.from_json(obj['bios'])
        host.bios.ps_computer_name = obj["computer_name"]
        host.computer_name = obj["computer_name"]
        if 'os' in obj:
            host.os = HostInfoWindowsVersion.from_json(obj["os"])
        else:
            host.os = HostInfoWindowsVersion(10,0,0,0,0,0)
        host.host_id = int(obj["host_id"]) if 'host_id' in obj  else 1000

        return host

    def edit_interactive(self):
        while True:
            answer = prompt([{'type': 'list','name': 'option','message': 'Editing host: ' + self.computer_name, 'choices' : ['Name','Disks','Bios','CPUs','Accounts','Network interfaces','Resume','Back','Cancel']}])
            if answer['option'] == 'Back':
                return self
            elif answer['option'] == 'Resume':
                print(self)
            elif answer['option'] == 'Cancel':
                return None
            elif answer['option'] == 'Disks':
                options =  ['Add']
                if len(self.disks) > 0:
                    options.append('Edit')
                    options.append('Delete')
                options.append('Back')
                answer = prompt([{'type': 'list','name': 'option','message': 'Modify disks', 'choices' : options}])

                if answer['option'] == 'Back':
                    continue
                elif answer['option'] == 'Add':
                    last_letter = 'B' if len(self.disks) == 0 else (self.disks[-1].device_id[0] + "")
                    disk = HostInfoDisk.create_interactive(last_letter)
                    if disk:
                        self.add_disk(disk)
                else:
                    disks = list(map(lambda x: x.device_id + ": " + x. volume_name, self.disks))
                    answer2 = prompt([{'type': 'list','name': 'option','message': 'Select a disk to edit', 'choices' :disks}])
                    pos = disks.index(answer2['option'])
                    if answer['option'] == 'Edit':
                        self.disks[pos].edit_interactive()
                    elif answer['option'] == 'Delete':
                        self.disks.pop(pos)
            elif answer['option'] == 'Bios':
                self.bios.edit_interactive()
            elif answer['option'] == 'Name':
                answer2 = prompt([{'type': 'input','name': 'option','message': 'Edit Hostname ', 'default' :str(self.computer_name)}])
                self.computer_name = answer2['option']
                self.bios.ps_computer_name = answer2['option']
            elif answer['option'] == 'Accounts':
                options =  ['Add']
                if len(self.accounts) > 0:
                    options.append('Edit')
                    options.append('Delete')
                    options.append('Remove service accounts')
                options.append('Back')
                answer = prompt([{'type': 'list','name': 'option','message': 'Modify accounts', 'choices' : options}])

                if answer['option'] == 'Back':
                    continue
                if answer['option'] == 'Remove service accounts':
                    self.accounts = filter_service_account(self.accounts)
                    continue
                elif answer['option'] == 'Add':
                    acc = HostInfoWindowsAccounts.create_interactive(self.computer_name)
                    if acc:
                        self.accounts.append(acc)
                else:
                    accounts = list(map(lambda x: x.name, self.accounts))
                    answer2 = prompt([{'type': 'list','name': 'option','message': 'Select an account to edit', 'choices' :accounts}])
                    pos = accounts.index(answer2['option'])
                    if answer['option'] == 'Edit':
                        self.accounts[pos].edit_interactive()
                    elif answer['option'] == 'Delete':
                        self.accounts.pop(pos)
            elif answer['option'] == 'Network interfaces':
                options =  ['Add']
                if len(self.networks) > 0:
                    options.append('Edit')
                    options.append('Delete')
                    options.append('Remove interfaces')
                options.append('Back')
                answer = prompt([{'type': 'list','name': 'option','message': 'Modify interfaces', 'choices' : options}])
                if answer['option'] == 'Back':
                    continue
                if answer['option'] == 'Remove interfaces':
                    self.networks = []
                    continue
                elif answer['option'] == 'Add':
                    ntwrk =  HostInfoNetwork.create_interactive(-1)
                    if ntwrk:
                        self.add_network(ntwrk)
                else:
                    networks = list(map(lambda x: x.description, self.networks))
                    answer2 = prompt([{'type': 'list','name': 'option','message': 'Select a interface to ' + answer['option'], 'choices' :networks}])
                    pos = networks.index(answer2['option'])
                    if answer['option'] == 'Edit':
                        self.networks[pos].edit_interactive()
                    elif answer['option'] == 'Delete':
                        self.networks.pop(pos)

            elif answer['option'] == 'CPUs':
                print("CPUs:\n" + "\n".join(list(map(lambda x: x.name, self.cpus))))
                options =  ['Add']
                if len(self.cpus) > 0:
                    options.append('Edit')
                    options.append('Delete')
                options.append('Back')
                answer = prompt([{'type': 'list','name': 'option','message': 'Modify CPUs', 'choices' : options}])
                if answer['option'] == 'Back':
                    continue
                elif answer['option'] == 'Add':
                    cpu =  HostInfoCpu("Intel(R) Core(TM) i5-8265U CPU @ 1.60GHz",4,8)
                    cpu = cpu.edit_interactive()
                    if cpu:
                        self.cpus.append(cpu)
                else:
                    cpus = list(map(lambda x: x.name, self.cpus))
                    answer2 = prompt([{'type': 'list','name': 'option','message': 'Select a CPU to ' + answer['option'], 'choices' :cpus}])
                    pos = cpus.index(answer2['option'])
                    if answer['option'] == 'Edit':
                        self.cpus[pos].edit_interactive()
                    elif answer['option'] == 'Delete':
                        self.cpus.pop(pos)
        return self


    def host_info_from_directory(scan_path):
        host = HostInfo()
        disk_path = os.path.join(scan_path, 'disk.json')

        if os.path.isfile(disk_path):
            with open(disk_path, 'r') as json_file:
                decoded_data = codecs.decode(json_file.read().encode(), 'utf-8-sig')
                data = json.loads(decoded_data)
                for disk in data:
                    if disk['DriveType'] == 3:
                        # Is HDD/SDD disk
                        host.disks.append(HostInfoDisk.from_json(disk))
        
        bios_path = os.path.join(scan_path, 'bios.json')
        if os.path.isfile(bios_path):
            with open(bios_path, 'r') as json_file:
                decoded_data = codecs.decode(json_file.read().encode(), 'utf-8-sig')
                bios = json.loads(decoded_data)
                if bios['Manufacturer']:
                    host.computer_name = bios['PSComputerName']
                    host.bios = HostInfoBios.from_json(bios)
                    # Build seabios with custom configuration

        net_path = os.path.join(scan_path, 'net.json')
        if os.path.isfile(net_path):
            with open(net_path,'r') as json_file:
                decoded_data = codecs.decode(json_file.read().encode(), 'utf-8-sig')
                net_file = json.loads(decoded_data)
                for net_iface in net_file:
                    if 'MACAddress' in net_iface and 'IPAddress' in net_iface and not net_iface['IPAddress'] == None:
                        host.networks.append(HostInfoNetwork.from_json(net_iface))

        version_path = os.path.join(scan_path, 'version.json')
        if os.path.isfile(version_path):
            with open(version_path, 'r') as json_file:
                decoded_data = codecs.decode(json_file.read().encode(), 'utf-8-sig')
                version_file = json.loads(decoded_data)
                customIf = {}
                if version_file['Major']:
                    host.so = HostInfoWindowsVersion.from_json(version_file)

        # Local accounts
        accounts_path = os.path.join(scan_path, 'accounts.json')
        if os.path.isfile(accounts_path):
            with open(accounts_path,'r') as json_file:
                decoded_data = codecs.decode(json_file.read().encode(), 'utf-8-sig')
                account_list = json.loads(decoded_data)
                for account in account_list:
                    if account['Name']:
                        host.accounts.append(HostInfoWindowsAccounts.from_json(account))

        # Lista de programas instalados
        programs_path = os.path.join(scan_path, 'programs.json')
        if os.path.isfile(programs_path):
            with open(programs_path, 'r') as json_file:
                decoded_data = codecs.decode(json_file.read().encode(), 'utf-8-sig')
                programs_file = json.loads(decoded_data)
                for program in programs_file:
                    if program['DisplayName']:
                        host.programs.append(HostInfoPrograms.from_json(program))

        return host


def size_textual_to_numeric(text):
    pattern = '^([0-9]+)([GMK])$'
    pattern = re.compile(pattern)
    convert = re.findall(pattern,text)
    if not convert or len(convert) != 1:
        raise Exception("Invalid format, must be: [0-9]+[GMKB]")
    total_size = 0
    convert = convert[0]
    if convert[1] == 'G':
        total_size = int(convert[0]) * 1000000000
    elif convert[1] == 'M':
        total_size = int(convert[0]) * 1000000
    elif convert[1] == 'K':
        total_size = int(convert[0]) * 1000
    elif convert[1] == 'B':
        total_size = int(convert[0])
    return total_size


def random_free_size(total_size):
    return random.randint(20*total_size, 60*total_size)

def next_letter(letter):
    print(letter)
    return chr(ord(letter) + 1) 

def size_numeric_to_textual(total_size):
    if total_size > 1000000000:
        size = int(total_size/1000000000)
        return str(size) + "G" 
    elif total_size > 1000000:
        size = int(total_size/1000000)
        return str(size) + "M" 
    elif total_size > 1000:
        size = int(total_size/1000)
        return str(size) + "K"
    
    return str(total_size)+"B" 

def filter_service_account(accounts):
    ret_acc = []
    for acc in accounts:
        if acc.name in ['WDAGUtilityAccount', 'DefaultAccount','Invitado','Guest']:
            continue
        if acc.name.startswith("SM_"):
            continue
        if acc.name.startswith("$_"):
            continue
        if acc.name.startswith("HealthMailbox"):
            continue
        ret_acc.append(acc)
    return ret_acc

def filter_kernel_interfaces(interfaces):
    ret_acc = []
    for acc in interfaces:
        if acc.description in ['WAN Miniport']:
            continue
        ret_acc.append(acc)
    return ret_acc