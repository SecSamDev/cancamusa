import os
import json
from PyInquirer import prompt
import bios_database
import re
import random
import codecs

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

class HostInfoDisk:
    def __init__(self, device_id, volume_name, size, free_space):
        self.device_id = device_id[0] # Only letter
        self.volume_name = volume_name
        self.size = size
        self.free_space = free_space
    
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
        print(obj)
        return HostInfoDisk(obj['DeviceID'], obj['VolumeName'], obj['Size'],obj['FreeSpace'])
        


class HostInfoNetwork:
    def __init__(self, net_object):
        if net_object:
            self.description = net_object['Description']
            self.setting_id = net_object['SettingID']
            self.mac_address = net_object['MACAddress']
            self.dns_domain = net_object['DNSDomain']
            self.dns_host_name = net_object['DNSHostName']
            self.index = net_object['Index']
            self.interfece_index = net_object['InterfaceIndex']
            self.ip_address = net_object['IPAddress']
    
    def edit_interactive(self):
        pass
    def to_json(self):
        return {
            'Description' : self.description,
            'SettingID' : self.setting_id,
            'MACAddress' : self.mac_address,
            'DNSDomain' : self.dns_domain,
            'DNSHostName' : self.dns_host_name,
            'Index' : self.index,
            'InterfaceIndex' : self.interfece_index,
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

    def __repr__(self):
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
        pass
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
    def __init__(self):
        self.disks = []
        self.bios = HostInfoBios(bios_database.BIOS_AMERICAN_MEGATREND_ALASKA_F5)
        self.computer_name = "Windows"
        self.networks = []
        self.so = HostInfoWindowsVersion(1,2,3,4,5,6)
        self.accounts = []
        self.programs = []
    
    def add_disk(self,disk):
        for dsk in self.disks:
            if dsk.device_id == disk.device_id:
                return
        self.disks.append(disk)

    
    def to_json(self):
        to_ret = {}
        to_ret['disks'] = []
        for disk in self.disks:
            to_ret['disk'].append(disk.to_json())
        to_ret['bios'] = self.bios.to_json()
        return to_ret

    def from_json(obj):
        host = HostInfo()
        for disk in obj['disks']:
            host.disks.append(HostInfoDisk.from_json(disk))
        host.bios = HostInfoBios.from_json(obj['bios'])

        return host

    def edit_interactive(self):
        while True:
            answer = prompt([{'type': 'list','name': 'option','message': 'Editing host: ' + self.computer_name, 'choices' : ['Disks','Bios','Back','Cancel']}])
            if answer['option'] == 'Back':
                return self
            elif answer['option'] == 'Cancel':
                return None
            elif answer['option'] == 'Disks':
                options =  ['Add','Back']
                if len(self.disks) > 0:
                    options.append('Edit')
                    options.append('Delete')
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
