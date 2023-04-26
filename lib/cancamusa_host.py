import os
import json
from PyInquirer import prompt
import bios_database
import re
import random
import codecs
from datetime import date

from mac_vendors import get_mac_list, search_wildcard_vendor, random_mac_for_vendor
from cancamusa_common import PASSWORD_GENERATOR_FIRSTNAME_YEAR, PASSWORD_GENERATOR_USERNAME_YEAR, random_guid, get_win_type
from rol_selector import AVAILABLE_ROLES, roles_from_extracted_info, ROLE_DNS, ROLE_DHCP,ROLE_KMS, ROLE_WEB_SERVER,ROLE_DOMAIN_CONTROLLER

from processors import list_processors

def read_host_information(pth):
    return HostInfo.host_info_from_directory(pth)


def read_host_files_in_path(pth):
    if not os.path.isdir(pth):
        raise Exception("Invalid host info path: " + path)

    host_in_dir = os.listdir(pth)
    host_list = []
    for host_dir in host_in_dir:
        try:
            host_list.append(read_host_information(
                os.path.join(pth, host_dir)))
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
        property_names = list(map(lambda x: str(x), dir(self)))
        class_props = list(map(lambda x: str(x), dir(HostInfoBios)))
        for element in class_props:
            property_names.pop(property_names.index(element))

        for prop in property_names:
            if prop.startswith("_"):
                continue
            answer = prompt([{'type': 'input', 'name': 'option', 'message': 'Edit: ' +
                              str(prop), 'default': str(getattr(self, prop))}])
            setattr(self, prop, answer['option'])
        return self

    def create_interactive():
        examples = ['Custom', 'Back'] + bios_database.BIOS_LIST
        answer = prompt([{'type': 'list', 'name': 'option',
                          'message': 'Select a bios: ' + self.ps_computer_name, 'choices': examples}])
        if answer['option'] == 'Custom':
            bios = HostInfoBios(
                bios_database.BIOS_AMERICAN_MEGATREND_ALASKA_F5)
            bios.edit_interactive()
            return bios
        if answer['option'] == 'Back':
            return

    def to_json(self):
        return {
            'Manufacturer': self.manufacturer,
            'Version': self.version,
            'Caption': self.caption,
            'Description': self.description,
            'ReleaseDate': self.release_date,
            'Name': self.name,
            'SoftwareElementID': self.software_element_id,
            'SoftwareElementState': self.software_element_state,
            'SystemBiosMajorVersion': self.system_bios_major_version,
            'SystemBiosMinorVersion': self.system_bios_minor_version,
            'SMBIOSMajorVersion': self.system_bios_minor_version,
            'SMBIOSMinorVersion': self.system_bios_minor_version,
            'EmbeddedControllerMajorVersion': self.embedded_controller_major_version,
            'EmbeddedControllerMinorVersion': self.embedded_controller_minor_version,
            'PSComputerName': self.ps_computer_name,
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
            'DisplayName': self.display_name,
            'DisplayVersion': self.display_version,
            'Publisher': self.publisher,
            'InstallDate': self.install_date
        }

    def from_json(obj):
        return HostInfoPrograms(obj['DisplayName'], obj['DisplayVersion'], obj['Publisher'], obj['InstallDate'])


class HostInfoRoles:
    def __init__(self, roles, config={}):
        self.roles = set()
        for rol in roles:
            self.roles.add(rol)
        self.config = config

    def edit_interactive(self):
        answer = prompt([{'type': 'checkbox', 'name': 'option',
                          'message': 'Select server roles: ', 'choices': [{'name': x, 'checked': (x in self.roles)} for x in AVAILABLE_ROLES]}])
        answ = answer['option']
        if len(answ) == 0:
            return
        else:
            for ans in answ:
                self.roles.add(ans)
        for rol in self.roles:
            # Customize properties for each ROL
            # DNS: DNS user and password for DHCP Server
            # Don't save state as to prevent errors
            self.config[rol] = {}
            if rol == ROLE_DOMAIN_CONTROLLER:
                answer = prompt([{'type': 'input', 'name': 'option',
                          'message': 'Safe mode password: ', 'default' : 'SafeModePassw123!'}])
                self.config[rol]['safe_mode_password'] = answer['option']
            if rol == ROLE_DNS:
                answer = prompt([{'type': 'input', 'name': 'option',
                          'message': 'Select username for DhcpServer in DNS: ', 'default' : 'dnsadmin'}])
                self.config[rol]['username'] = answer['option']
                answer = prompt([{'type': 'input', 'name': 'option',
                          'message': 'Select password for DhcpServer in DNS: ', 'default' : 'password'}])
                self.config[rol]['password'] = answer['option']
                answer = prompt([{'type': 'input', 'name': 'option',
                          'message': 'External DNS server: ', 'default' : '8.8.8.8'}])
                self.config[rol]['forwarder'] = answer['option']
            if rol == ROLE_DHCP:
                answer = prompt([{'type': 'list', 'name': 'option',
                          'message': 'Failover mode: ', 'choices' : ['StandBy','Active']}])
                self.config[rol]['failover_mode'] = answer['option']
                if self.config[rol]['failover_mode'] == 'Active':
                    answer = prompt([{'type': 'input', 'name': 'option',
                            'message': 'Failover secret: ', 'default' : 'S3cret'}])
                    self.config[rol]['failover_secret'] = answer['option']
            if rol == ROLE_WEB_SERVER:
                # TODO
                self.config[rol] = {}
            if rol == ROLE_KMS:
                if not 'license_keys' in self.config[rol]:
                    self.config[rol]['license_keys'] = {}
                while True:
                    answer = prompt([{'type': 'list', 'name': 'option','message': 'Failover mode: ', 'choices' : ['Add','Remove','List','Exit']}])
                    # https://docs.microsoft.com/en-us/deployoffice/vlactivation/configure-a-kms-host-computer-for-office
                    if answer['option'] == 'Add':
                        answer = prompt([{'type': 'input', 'name': 'option', 'message': 'Windows Activation ID: ', 'default' : ''}])
                        answer2 = prompt([{'type': 'input', 'name': 'option', 'message': 'Windows Confirmation ID: ', 'default' : ''}])
                        self.config[rol]['license_keys'][answer['option']] = answer2['option']
                    elif answer['option'] == 'Remove':
                        answer = prompt([{'type': 'list', 'name': 'option','message': 'ActivationID: ', 'choices' : list(self.config[rol]['license_keys'].keys()) }])
                        self.config[rol]['license_keys'].pop(answer['option'],None)
                    elif answer['option'] == 'List':
                        print("{}".format(", ".join(list(self.config[rol]['license_keys'].keys()))))
                    elif answer['option'] == 'Exit':
                        break
            
        return self

    def create_interactive():
        roles = set()
        answer = prompt([{'type': 'checkbox', 'name': 'option',
                          'message': 'Select server roles: ', 'choices': [{'name': x, 'checked': (x in self.roles)} for x in AVAILABLE_ROLES]}])
        answ = answer['option']
        if len(answ) == 0:
            return HostInfoRoles([])
        else:
            for ans in answ:
                roles.add(ans)
            return HostInfoRoles(roles)

    def to_json(self):
        toRet = []
        for rol in self.roles:
            config = self.config[rol] if rol in self.config else {}
            toRet.append({
                'Name': rol,
                'Config' : config
            })
        return toRet

    def from_json(roles):
        if len(roles) > 0 and 'Name' in roles[0] and not 'DisplayName' in roles[0]:
            rols = []
            configs = {}
            for rol in roles:
                config = rol['Config'] if 'Config' in rol else {}
                configs[rol['Name']] = config
                rols.append(rol['Name'])
            return HostInfoRoles(rols, configs)
        elif len(roles) > 0 and 'Name' in roles[0] and 'DisplayName' in roles[0]:
            # Not processed
            role_list = roles_from_extracted_info(roles)
            return HostInfoRoles(role_list)
        else:
            return HostInfoRoles([])


class HostInfoDisk:
    def __init__(self, device_id, volume_name, size, free_space):
        self.device_id = device_id[0]  # Only letter
        self.volume_name = volume_name
        self.size = size
        self.free_space = free_space

    def __str__(self):
        return "{}: {} ({})".format(self.device_id, self.volume_name, size_numeric_to_textual(self.size))

    def edit_interactive(self):
        answer = prompt([{'type': 'input', 'name': 'option',
                          'message': 'Select device ID', 'default': self.device_id}])
        if len(answer['option']) != 1:
            print("Drive letter must be 1 character long")
            return
        else:
            self.device_id = answer['option']
        answer = prompt([{'type': 'input', 'name': 'option',
                          'message': 'Volume name', 'default': self.volume_name}])
        self.volume_name = answer['option']
        answer = prompt([{'type': 'input', 'name': 'option', 'message': 'Disk Size.',
                          'default': size_numeric_to_textual(self.size)}])
        size = size_textual_to_numeric(answer['option'])
        self.size = size
        self.free_space = random_free_size(size)
        return self

    def create_interactive(last_leter="B", computer_name="My PC"):
        disk = HostInfoDisk(next_letter(last_leter), computer_name, 64098583552, 20828822016)
        disk = disk.edit_interactive()
        return disk

    def to_json(self):
        return {
            'DeviceID': self.device_id,
            'VolumeName': self.volume_name,
            'Size': self.size,
            'FreeSpace': self.free_space
        }

    def from_json(obj):
        return HostInfoDisk(obj['DeviceID'], obj['VolumeName'], obj['Size'], obj['FreeSpace'])


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
                self.ip_address = ['192.168.0.2']
            if 'IPSubnet' in net_object and net_object['IPSubnet'] and isinstance(net_object['IPSubnet'], list):
                self.ip_subnet = net_object['IPSubnet']
            else:
                self.ip_subnet = ['255.255.255.0']
            if 'DefaultIPGateway' in net_object and net_object['DefaultIPGateway'] and isinstance(net_object['DefaultIPGateway'], list):
                self.ip_gateway = net_object['DefaultIPGateway']
            else:
                self.ip_gateway = ['192.168.0.1']
            if 'AssignMethod' in net_object:
                self.assign_method = net_object['AssignMethod']
            else:
                # static, dynamic, DHCP
                self.assign_method = 'static'
            if 'DNSServers' in net_object:
                self.dns_servers = net_object['DNSServers']
            else:
                self.dns_servers = [self.ip_gateway[0],'8.8.4.4']            

    def __str__(self):
        return "{}: {} ({}) [{}]".format(self.index, self.description, self.mac_address, ",".join(self.ip_address))

    def edit_interactive(self):
        property_names = list(map(lambda x: str(x), dir(self)))
        class_props = list(map(lambda x: str(x), dir(HostInfoNetwork)))
        for element in class_props:
            property_names.pop(property_names.index(element))

        for prop in property_names:
            if prop.startswith("_"):
                continue
            if prop in ['setting_id','index','interface_index']:
                continue
            if prop == 'assign_method':
                answer = prompt([{'type': 'list', 'name': 'option',
                                  'message': 'Edit IP assignation method',  'choices': [
                        'static', 'dynamic', 'fixed']}])
                self.assign_method = answer['option']
                continue
            if prop == 'ip_address':
                answer = prompt([{'type': 'input', 'name': 'option',
                                  'message': 'Edit IpAddress', 'default': str(getattr(self, prop))}])
                to_parse = answer['option'].strip()
                if to_parse.startswith("["):
                    to_parse = to_parse[1:]
                if to_parse.endswith("]"):
                    to_parse = to_parse[:-1]
                split = list(map(lambda x: x.replace(
                    "'", '').strip(), to_parse.split(',')))
                self.ip_address = split
                continue
            if prop == 'ip_subnet':
                answer = prompt([{'type': 'input', 'name': 'option',
                                  'message': 'Edit Subnet', 'default': str(getattr(self, prop))}])
                to_parse = answer['option'].strip()
                if to_parse.startswith("["):
                    to_parse = to_parse[1:]
                if to_parse.endswith("]"):
                    to_parse = to_parse[:-1]
                split = list(map(lambda x: x.replace(
                    "'", '').strip(), to_parse.split(',')))
                self.ip_subnet = split
                continue
            if prop == 'ip_gateway':
                answer = prompt([{'type': 'input', 'name': 'option',
                                  'message': 'Edit Gateway', 'default': str(getattr(self, prop))}])
                to_parse = answer['option'].strip()
                if to_parse.startswith("["):
                    to_parse = to_parse[1:]
                if to_parse.endswith("]"):
                    to_parse = to_parse[:-1]
                split = list(map(lambda x: x.replace(
                    "'", '').replace('[','').replace(']','').strip(), to_parse.split(',')))
                self.ip_gateway = split
                continue
            if prop == 'dns_servers':
                answer = prompt([{'type': 'input', 'name': 'option',
                                  'message': 'Edit Gateway', 'default': str(getattr(self, prop))}])
                to_parse = answer['option'].strip()
                if to_parse.startswith("["):
                    to_parse = to_parse[1:]
                if to_parse.endswith("]"):
                    to_parse = to_parse[:-1]
                split = list(map(lambda x: x.replace(
                    "'", '').replace('[','').replace(']','').strip(), to_parse.split(',')))
                self.dns_servers = split
                continue
            answer = prompt([{'type': 'input', 'name': 'option', 'message': 'Edit: ' +
                              str(prop), 'default': str(getattr(self, prop))}])
            setattr(self, prop, answer['option'])
        self.index = int(self.index)
        self.interface_index = int(self.interface_index)
        return self

    def create_interactive(last_index=-1):
        answer = prompt([{'type': 'list', 'name': 'option', 'message': 'Network edition mode', 'choices': [
                        'Random device', 'Search vendor', 'Basic']}])
        netwrk = None
        if answer['option'] == 'Random device':
            device = search_wildcard_vendor(get_mac_list(), '*')
            netwrk = HostInfoNetwork({
                'Description': device['vendor'],
                'SettingID': "{" + random_guid() + "}",
                'MACAddress': random_mac_for_vendor(device['mac']),
                'DNSDomain': '',
                'DNSHostName': '',
                'Index': int(last_index) + 1,
                'InterfaceIndex': int(last_index) + 1,
                'IPAddress': ["192.168.0.2"],
                'IPSubnet' : ["255.255.255.0"],
                'DefaultIPGateway' : ["192.168.0.1"],
                'AssignMethod' : 'static',
                'DNSServers' : ['8.8.8.8','8.8.4.4']
            })
        elif answer['option'] == 'Search vendor':
            while True:
                mac_list = get_mac_list()
                device = search_wildcard_vendor(mac_list, '*')
                answer = prompt(
                    [{'type': 'input', 'name': 'option', 'message': 'Search by vendor name'}])
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
                answer = prompt(
                    [{'type': 'list', 'name': 'option', 'message': 'Select a vendor', 'choices': names}])
                pos = names.index(answer['option'])

                netwrk = HostInfoNetwork({
                    'Description': names[pos],
                    'SettingID':  "{" + random_guid() + "}",
                    'MACAddress': random_mac_for_vendor(macs[pos]),
                    'DNSDomain': '',
                    'DNSHostName': '',
                    'Index': int(last_index) + 1,
                    'InterfaceIndex': int(last_index) + 1,
                    'IPAddress': ["192.168.0.2"],
                    'IPSubnet' : ["255.255.255.0"],
                    'DefaultIPGateway' : ["192.168.0.1"],
                    'AssignMethod' : 'static',
                    'DNSServers' : ['8.8.8.8','8.8.4.4']
                })
                break
        elif answer['option'] == 'Basic':
            netwrk = HostInfoNetwork({
                'Description': 'Killer E2200 Gigabit Ethernet Controller',
                'SettingID':  "{" + random_guid() + "}",
                'MACAddress': random_mac_for_vendor(search_wildcard_vendor(get_mac_list(), 'FCAA14')['mac']),
                'DNSDomain': '',
                'DNSHostName': '',
                'Index': int(last_index) + 1,
                'InterfaceIndex': int(last_index) + 1,
                'IPAddress': ["192.168.0.2"],
                'IPSubnet' : ["255.255.255.0"],
                'DefaultIPGateway' : ["192.168.0.1"],
                'AssignMethod' : 'static',
                'DNSServers' : ['8.8.8.8','8.8.4.4']
            })
        netwrk = netwrk.edit_interactive()
        return netwrk

    def to_json(self):
        return {
            'Description': self.description,
            'SettingID': self.setting_id,
            'MACAddress': self.mac_address,
            'DNSDomain': self.dns_domain,
            'DNSHostName': self.dns_host_name,
            'Index': int(self.index),
            'InterfaceIndex': int(self.interface_index),
            'IPAddress': self.ip_address,
            'IPSubnet' : self.ip_subnet,
            'DefaultIPGateway' : self.ip_gateway,
            'AssignMethod' : self.assign_method,
            'DNSServers' : self.dns_servers
        }

    def from_json(net_object):
        return HostInfoNetwork(net_object)


class HostInfoWindowsVersion:
    def __init__(self, name, major, minor, build, revision, major_revision, minor_revision):
        self.name = name
        self.major = major
        self.minor = minor
        self.build = build
        self.revision = revision
        self.major_revision = major_revision
        self.minor_revision = minor_revision
        self.win_type = get_win_type(self.name)

    def __str__(self):
        return "{} ({})".format(self.name, self.build)

    def edit_interactive(self):
        answer = prompt([{'type': 'list', 'name': 'option',
            'message': 'Select a Windows type:', 'choices': ['Basic Edit','Full Edit']}])
        if answer['option'] == 'Basic Edit':
            answer = prompt([{'type': 'list', 'name': 'option',
            'message': 'Select a Windows type:', 'choices': ['Win7','Win8.1','Win10','Win11','Win2008r2','Win2012r2','Win2016','Win2019']}])
            if answer['option'] == 'Win10':
                self.name = 'Windows 10'
                self.major = 10
                self.minor = 0
                self.build = 1909
                self.revision = 18363
                self.major_revision = 1
                self.minor_revision = 0
            elif answer['option'] == 'Win11':
                self.name = 'Windows 11'
                self.major = 10
                self.minor = 0
                self.build = 1909
                self.revision = 18363
                self.major_revision = 1
                self.minor_revision = 0
            elif answer['option'] == 'Win7':
                self.name = 'Windows 7'
                self.major = 6
                self.minor = 1
                self.build = 7601
                self.revision = 65536
                self.major_revision = 1
                self.minor_revision = 0
            elif answer['option'] == 'Win8.1':
                self.name = 'Windows 8.1'
                self.major = 6
                self.minor = 1
                self.build = 7601
                self.revision = 65536
                self.major_revision = 1
                self.minor_revision = 0
            elif answer['option'] == 'Win2008r2':
                self.name = 'Windows Server 2008 R2'
                self.major = 6
                self.minor = 1
                self.build = 7600
                self.revision = 1
                self.major_revision = 1
                self.minor_revision = 0
            elif answer['option'] == 'Win2012r2':
                self.name = 'Windows Server 2012 R2'
                self.major = 6
                self.minor = 2
                self.build = 7600
                self.revision = 1
                self.major_revision = 1
                self.minor_revision = 0
            elif answer['option'] == 'Win2016':
                self.name = 'Windows Server 2016'
                self.major = 10
                self.minor = 0
                self.build = 14393
                self.revision = 1607
                self.major_revision = 1
                self.minor_revision = 0
            elif answer['option'] == 'Win2019':
                self.name = 'Windows Server 2019'
                self.major = 10
                self.minor = 0
                self.build = 19041
                self.revision = 1
                self.major_revision = 1
                self.minor_revision = 0
            
            self.win_type = answer['option']
        else:
            answer = prompt([{'type': 'input', 'name': 'option',
                'message': 'Select OS name', 'default': self.name}])
            self.name = answer['option']
            answer = prompt([{'type': 'input', 'name': 'option',
                'message': 'Select OS Major Version', 'default': str(self.major)}])
            self.major = int(answer['option'])
            answer = prompt([{'type': 'input', 'name': 'option',
                'message': 'Select OS Minor Version', 'default': str(self.minor)}])
            self.minor = int(answer['option'])
            answer = prompt([{'type': 'input', 'name': 'option',
                'message': 'Select OS Build Version', 'default': str(self.build)}])
            self.build = answer['option']
            answer = prompt([{'type': 'input', 'name': 'option',
                'message': 'Select OS revision Version', 'default': str(self.revision)}])
            self.revision = answer['option']
            answer = prompt([{'type': 'input', 'name': 'option',
                'message': 'Select OS major revision Version', 'default': str(self.major_revision)}])
            self.major_revision = int(answer['option'])
            answer = prompt([{'type': 'input', 'name': 'option',
                'message': 'Select OS minor revision Version', 'default': str(self.minor_revision)}])
            self.minor_revision = int(answer['option'])
        pass

    def to_json(self):
        return {
            'Name': self.name,
            'Major': self.major,
            'Minor': self.minor,
            'Build': self.build,
            'Revision': self.revision,
            'MajorRevision': self.major_revision,
            'MinorRevision': self.minor_revision
        }

    def from_json(version_file):
        if not 'Name' in version_file:
            version_file['Name'] = 'Windows 10 Enterprise'
        return HostInfoWindowsVersion(version_file['Name'], version_file['Major'], version_file['Minor'], version_file['Build'], version_file['Revision'], version_file['MajorRevision'], version_file['MinorRevision'])


class HostInfoCpu:
    def __init__(self, name, cores, threads):
        self.name = name
        self.family = "Intel"
        self.cores = cores
        self.threads = threads
        self.processor_type = "Haswell"
        self.architecture = "x64"

    def __str__(self):
        return "{} {} {}/{}".format(self.name,self.architecture, self.cores, self.threads)

    def edit_interactive(self):
        answer = prompt([{'type': 'input', 'name': 'option',
                          'message': 'Select CPU name', 'default': self.name}])
        self.name = answer['option']
        self.detect_cpu_family()
        answer = prompt([{'type': 'input', 'name': 'option',
                          'message': 'Cores:', 'default': str(self.cores)}])
        self.cores = int(answer['option'])
        answer = prompt([{'type': 'input', 'name': 'option',
                          'message': 'Threads: ', 'default': str(self.threads)}])
        self.threads = int(answer['option'])
        answer = prompt([{'type': 'list', 'name': 'option',
            'message': 'Select a processor architecture:', 'choices': ['x86','x64','ARM64']}])
        self.architecture = answer['option']
        #answer = prompt([{'type': 'list', 'name': 'option','message': 'Select a QEMU cpu type:', 'choices': list_processors(self.family)}])
        #self.processor_type = answer['option']
        return self
    
    def safe_name(self):
        return re.sub(r'[^a-zA-Z0-9]',"",self.name)

    def detect_cpu_family(self):
        if 'Intel' in self.name:
            self.family = "Intel"
        elif 'AMD' in self.name:
            self.family = "AMD"
        else:
            self.family = None

    def to_json(self):
        return {
            'Name': self.name,
            'NumberOfCores': self.cores,
            'NumberOfLogicalProcessors': self.threads,
            'Family': self.family,
            'CpuType': self.processor_type,
            "Architecture" : self.architecture
        }

    def from_json(version_file):
        host = HostInfoCpu(version_file['Name'], version_file['NumberOfCores'], version_file['NumberOfLogicalProcessors'])
        if "Architecture" in version_file:
            host.architecture = version_file["Architecture"]
        return host

class HostInfoRAM:
    def __init__(self, manufacturer,capacity):
        self.manufacturer = manufacturer
        self.capacity = int(capacity)

    def __str__(self):
        return "{} {}".format(self.manufacturer,size_numeric_to_textual(self.capacity))

    def edit_interactive(self):
        answer = prompt([{'type': 'input', 'name': 'option',
                          'message': 'Manufacturer', 'default': self.manufacturer}])
        self.manufacturer = answer['option']
        answer = prompt([{'type': 'input', 'name': 'option',
                          'message': 'Capacity:', 'default': str(size_numeric_to_textual(self.capacity))}])
        self.capacity = int(size_textual_to_numeric(answer['option']))
        
        return self

    def to_mib(self):
        return int(self.capacity / 1000000)

    def to_json(self):
        return {
            'Manufacturer': self.manufacturer,
            'Capacity': self.capacity,
        }

    def from_json(version_file):
        return HostInfoRAM(version_file['Manufacturer'], int(version_file['Capacity']))


class HostInfoWindowsAccounts:
    def __init__(self, account, password_generator=PASSWORD_GENERATOR_FIRSTNAME_YEAR):
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
        if 'Password' in account:
            self.password = account['Password']
        else:
            self.password = 'CancamusaRocks123!'
        if 'Domain' in account:
            self.domain = account['Domain']
        else:
            self.domain = self.ps_computer_name
        self.password_generator = password_generator

    def edit_interactive(self, password_generator=PASSWORD_GENERATOR_FIRSTNAME_YEAR):
        # If needed change in cancamusa.json
        """
        property_names = list(map(lambda x: str(x), dir(self)))
        class_props = list(map(lambda x: str(x), dir(HostInfoWindowsAccounts)))
        for element in class_props:
            property_names.pop(property_names.index(element))
        """
        property_names = ['name','description','domain','password']
        for prop in property_names:
            if prop.startswith("_"):
                continue
            if prop == 'password':
                if self.password_generator == PASSWORD_GENERATOR_FIRSTNAME_YEAR:
                    self.password = self.name + str(date.today().year)
                elif self.password_generator == PASSWORD_GENERATOR_USERNAME_YEAR:
                    self.password = self.name + str(date.today().year)
            answer = prompt([{'type': 'input', 'name': 'option', 'message': 'Edit: ' +
                              str(prop), 'default': str(getattr(self, prop))}])
            setattr(self, prop, answer['option'])
        return self

    def __str__(self):
        return "{} : {}".format(self.name, self.description)

    def create_interactive(host_name="", password_generator=PASSWORD_GENERATOR_FIRSTNAME_YEAR):
        disk = HostInfoWindowsAccounts({
            'Name': 'Administrator',
            'LocalAccount': True,
            'AccountType': 512,
            'PSComputerName': host_name,
            'Description': "Cuenta integrada para el acceso como invitado al equipo o dominio",
            'SID': 'S-1-5-21-2718119982-1426233563-2378531167-500',
            'Lockout': False,
            'PasswordChangeable': True,
            'PasswordExpires': False,
            'PasswordRequired': True,
            'Domain' : host_name,
            'Password' : 'password'
        })
        disk = disk.edit_interactive(password_generator=password_generator)
        return disk

    def to_json(self):
        return {
            'Name': self.name,
            'LocalAccount': self.local_account,
            'AccountType': self.account_type,
            'PSComputerName': self.ps_computer_name,
            'Description': self.description,
            'SID': self.sid,
            'Lockout': self.lockout,
            'PasswordChangeable': self.password_changeable,
            'PasswordExpires': self.password_expires,
            'PasswordRequired': self.password_required,
            'Domain' : self.domain,
            'Password' : self.password
        }

    def from_json(account):
        return HostInfoWindowsAccounts(account)


class HostInfo:
    def __init__(self, host_id=1000, password_generator='CancamusaRocks123!',default_language="en-EN"):
        self.host_id = host_id
        self.disks = []
        self.bios = HostInfoBios(
            bios_database.BIOS_AMERICAN_MEGATREND_ALASKA_F5)
        self.computer_name = ""
        self.networks = []
        self.os = HostInfoWindowsVersion('Windows 10 Enterprise',10, 0, 0, 0, 0, 0)
        self.accounts = []
        self.programs = []
        self.roles = HostInfoRoles([])
        self.cpus = []
        self.ram = HostInfoRAM("Crucial",size_textual_to_numeric("4G"))
        self.domain = None
        self.selected_img_idx = None
        self.selected_img_pth = None
        self.language = default_language
        self.password_generator = password_generator

    def set_language(self):
        answer = prompt([{'type': 'input', 'name': 'option','message': 'Set Windows Language (en-EN) ', 'default': str(self.language)}])
        self.language = answer['option']

    def get_account_for_domain(self, domain):
        for acc in self.accounts:
            if acc.domain == domain:
                return acc
        return None

    def add_disk(self, disk):
        for dsk in self.disks:
            if dsk.device_id == disk.device_id:
                return
        self.disks.append(disk)

    def add_network(self, net):
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
        to_ret += "Disks:\n"
        for disk in self.disks:
            to_ret += "\t{}\n".format(disk)
        to_ret += "Accounts:\n"
        for acc in self.accounts:
            to_ret += "\t{}\n".format(acc)
        to_ret += "Network Interfaces:\n"
        for nt in self.networks:
            to_ret += "\t{}\n".format(nt)
        to_ret += "CPUs:\n"
        for nt in self.cpus:
            to_ret += "\t{}\n".format(nt)
        to_ret += "RAM:\n\t{}\n".format(self.ram)
        return to_ret

    def to_json(self):
        to_ret = {
            'host_id': self.host_id,
            'cpus': [],
            'ram' : self.ram.to_json()
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
        to_ret['roles'] = self.roles.to_json()
        to_ret["os"] = self.os.to_json()
        to_ret["computer_name"] = self.computer_name[0:min(15, len(self.computer_name))]
        to_ret["domain"] = self.domain
        if self.selected_img_idx != None:
            to_ret['selected_img_idx'] = self.selected_img_idx
        if self.selected_img_pth != None:
            to_ret['selected_img_pth'] = self.selected_img_pth
        to_ret['language'] = self.language
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
        if 'os' in obj:
            host.os = HostInfoWindowsVersion.from_json(obj["os"])
        else:
            host.os = HostInfoWindowsVersion('Windows 10 Enterprise',10, 0, 0, 0, 0, 0)
        if len(host.cpus) == 0:
            if host.os.win_type in ['win10', 'win7','win11']:
                host.cpus.append(HostInfoCpu(
                    "Intel(R) Core(TM) i5-8265U CPU @ 1.60GHz", 4, 8))
            else:
                host.cpus.append(HostInfoCpu(
                    "Intel(R) Xeon(R) CPU E5-2430L v2 @ 2.40GHz", 6, 12))
        host.bios = HostInfoBios.from_json(obj['bios'])
        host.bios.ps_computer_name = obj["computer_name"]
        host.computer_name = obj["computer_name"]
        host.host_id = int(obj["host_id"]) if 'host_id' in obj else 1000
        host.ram = HostInfoRAM.from_json(obj['ram'])
        host.domain = obj['domain']
        host.roles = HostInfoRoles.from_json(obj['roles'])
        if 'selected_img_idx' in obj:
            host.selected_img_idx = obj['selected_img_idx']
        if 'selected_img_pth' in obj:
            host.selected_img_pth = obj['selected_img_pth']
        host.domain = obj['domain']
        if 'language' in obj:
            host.language = obj['language']
        return host

    def edit_interactive(self, project=None):
        while True:
            answer = prompt([{'type': 'list', 'name': 'option', 'message': 'Editing host: ' + self.computer_name, 'choices': [
                            'Name', 'Disks', 'Bios','RAM', 'CPUs', 'Accounts','Language','Domain','Roles', 'Network interfaces', 'OS Version', 'Resume', 'Back', 'Cancel']}])
            if answer['option'] == 'Back':
                return self
            elif answer['option'] == 'Resume':
                print(self)
            elif answer['option'] == 'Cancel':
                return None
            elif answer['option'] == 'Language':
                self.set_language()
            elif answer['option'] == 'Disks':
                options = ['Add']
                if len(self.disks) > 0:
                    options.append('Edit')
                    options.append('Delete')
                options.append('Back')
                answer = prompt(
                    [{'type': 'list', 'name': 'option', 'message': 'Modify disks', 'choices': options}])

                if answer['option'] == 'Back':
                    continue
                elif answer['option'] == 'Add':
                    last_letter = 'B' if len(self.disks) == 0 else (
                        self.disks[-1].device_id[0] + "")
                    disk = HostInfoDisk.create_interactive(last_letter, computer_name=self.computer_name)
                    if disk:
                        self.add_disk(disk)
                else:
                    disks = list(map(lambda x: x.device_id +
                                     ": " + x. volume_name, self.disks))
                    answer2 = prompt(
                        [{'type': 'list', 'name': 'option', 'message': 'Select a disk to edit', 'choices': disks}])
                    pos = disks.index(answer2['option'])
                    if answer['option'] == 'Edit':
                        self.disks[pos].edit_interactive()
                    elif answer['option'] == 'Delete':
                        self.disks.pop(pos)
            elif answer['option'] == 'Bios':
                self.bios.edit_interactive()
            elif answer['option'] == 'Domain':
                if project:
                    domains = list(map(lambda x: x.domain, project.domain.domains)) + ["None"]
                    answer2 = prompt([{'type': 'list', 'name': 'option', 'message': 'Join a domain', 'choices': domains}])
                    pos = domains.index(answer2['option'])
                    if domains[pos] == "None":
                        self.domain = None
                    else:
                        self.domain = domains[pos]
                else:
                    print("No domains available...")
            elif answer['option'] == 'Roles':
                if self.os.win_type.lower() in ['win2008r2','win2012r2','win2016','win2019']:
                    self.roles.edit_interactive()
                else:
                    print(self.os.win_type)
                    print("This is not a server")
            elif answer['option'] == 'RAM':
                self.ram.edit_interactive()
            elif answer['option'] == 'OS Version':
                self.os.edit_interactive()
            elif answer['option'] == 'Name':
                answer2 = prompt([{'type': 'input', 'name': 'option',
                                   'message': 'Edit Hostname ', 'default': str(self.computer_name)}])
                self.computer_name = answer2['option']
                self.computer_name = self.computer_name[0:min(15, len(self.computer_name))]
                self.bios.ps_computer_name = answer2['option']
            elif answer['option'] == 'Accounts':
                options = ['Add']
                if len(self.accounts) > 0:
                    options.append('Edit')
                    options.append('Delete')
                    options.append('Remove service accounts')
                options.append('Back')
                answer = prompt([{'type': 'list', 'name': 'option',
                                  'message': 'Modify accounts', 'choices': options}])

                if answer['option'] == 'Back':
                    continue
                if answer['option'] == 'Remove service accounts':
                    self.accounts = filter_service_account(self.accounts)
                    continue
                elif answer['option'] == 'Add':
                    acc = HostInfoWindowsAccounts.create_interactive(
                        self.computer_name, password_generator=self.password_generator)
                    if acc:
                        self.accounts.append(acc)
                else:
                    accounts = list(map(lambda x: x.name, self.accounts))
                    answer2 = prompt(
                        [{'type': 'list', 'name': 'option', 'message': 'Select an account to edit', 'choices': accounts}])
                    pos = accounts.index(answer2['option'])
                    if answer['option'] == 'Edit':
                        self.accounts[pos].edit_interactive()
                    elif answer['option'] == 'Delete':
                        self.accounts.pop(pos)
            elif answer['option'] == 'Network interfaces':
                options = ['Add']
                if len(self.networks) > 0:
                    options.append('Edit')
                    options.append('Delete')
                    options.append('Remove interfaces')
                options.append('Back')
                answer = prompt([{'type': 'list', 'name': 'option',
                                  'message': 'Modify interfaces', 'choices': options}])
                if answer['option'] == 'Back':
                    continue
                if answer['option'] == 'Remove interfaces':
                    self.networks = []
                    continue
                elif answer['option'] == 'Add':
                    ntwrk = HostInfoNetwork.create_interactive(-1)
                    if ntwrk:
                        self.add_network(ntwrk)
                else:
                    networks = list(
                        map(lambda x: x.description, self.networks))
                    answer2 = prompt(
                        [{'type': 'list', 'name': 'option', 'message': 'Select a interface to ' + answer['option'], 'choices':networks}])
                    pos = networks.index(answer2['option'])
                    if answer['option'] == 'Edit':
                        self.networks[pos].edit_interactive()
                    elif answer['option'] == 'Delete':
                        self.networks.pop(pos)

            elif answer['option'] == 'CPUs':
                print("CPUs:\n" + "\n".join(list(map(lambda x: x.name, self.cpus))))
                options = ['Add']
                if len(self.cpus) > 0:
                    options.append('Edit')
                    options.append('Delete')
                options.append('Back')
                answer = prompt(
                    [{'type': 'list', 'name': 'option', 'message': 'Modify CPUs', 'choices': options}])
                if answer['option'] == 'Back':
                    continue
                elif answer['option'] == 'Add':
                    cpu = HostInfoCpu(
                        "Intel(R) Core(TM) i5-8265U CPU @ 1.60GHz", 4, 8)
                    cpu = cpu.edit_interactive()
                    if cpu:
                        self.cpus.append(cpu)
                else:
                    cpus = list(map(lambda x: x.name, self.cpus))
                    answer2 = prompt(
                        [{'type': 'list', 'name': 'option', 'message': 'Select a CPU to ' + answer['option'], 'choices':cpus}])
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
                decoded_data = codecs.decode(
                    json_file.read().encode(), 'utf-8-sig')
                data = json.loads(decoded_data)
                for disk in data:
                    if disk['DriveType'] == 3:
                        # Is HDD/SDD disk
                        host.disks.append(HostInfoDisk.from_json(disk))

        bios_path = os.path.join(scan_path, 'bios.json')
        if os.path.isfile(bios_path):
            with open(bios_path, 'r') as json_file:
                decoded_data = codecs.decode(
                    json_file.read().encode(), 'utf-8-sig')
                bios = json.loads(decoded_data)
                if bios['Manufacturer']:
                    host.computer_name = bios['PSComputerName']
                    host.bios = HostInfoBios.from_json(bios)
                    # Build seabios with custom configuration

        net_path = os.path.join(scan_path, 'net.json')
        if os.path.isfile(net_path):
            with open(net_path, 'r') as json_file:
                decoded_data = codecs.decode(
                    json_file.read().encode(), 'utf-8-sig')
                net_file = json.loads(decoded_data)
                for net_iface in net_file:
                    if 'MACAddress' in net_iface and 'IPAddress' in net_iface and not net_iface['IPAddress'] == None:
                        host.networks.append(
                            HostInfoNetwork.from_json(net_iface))

        version_path = os.path.join(scan_path, 'version.json')
        if os.path.isfile(version_path):
            with open(version_path, 'r') as json_file:
                decoded_data = codecs.decode(
                    json_file.read().encode(), 'utf-8-sig')
                version_file = json.loads(decoded_data)
                customIf = {}
                if version_file['Major']:
                    host.so = HostInfoWindowsVersion.from_json(version_file)

        # Local accounts
        accounts_path = os.path.join(scan_path, 'accounts.json')
        if os.path.isfile(accounts_path):
            with open(accounts_path, 'r') as json_file:
                decoded_data = codecs.decode(
                    json_file.read().encode(), 'utf-8-sig')
                account_list = json.loads(decoded_data)
                for account in account_list:
                    if account['Name']:
                        host.accounts.append(
                            HostInfoWindowsAccounts.from_json(account))

        # Lista de programas instalados
        programs_path = os.path.join(scan_path, 'programs.json')
        if os.path.isfile(programs_path):
            with open(programs_path, 'r') as json_file:
                decoded_data = codecs.decode(
                    json_file.read().encode(), 'utf-8-sig')
                programs_file = json.loads(decoded_data)
                for program in programs_file:
                    if program['DisplayName']:
                        host.programs.append(
                            HostInfoPrograms.from_json(program))

        return host


def size_textual_to_numeric(text):
    pattern = '^([0-9]+)([GMKB])$'
    pattern = re.compile(pattern)
    convert = re.findall(pattern, text)
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
        if (total_size % 1000000000) < 100000000:
            return str(size) + "G"
    elif total_size > 1000000:
        size = int(total_size/1000000)
        if (total_size % 1000000) < 1000:
            return str(size) + "M"
    elif total_size > 1000:
        size = int(total_size/1000)
        return str(size) + "K"

    return str(total_size)+"B"


def filter_service_account(accounts):
    ret_acc = []
    for acc in accounts:
        if acc.name in ['WDAGUtilityAccount', 'DefaultAccount', 'Invitado', 'Guest']:
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
