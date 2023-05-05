from PyInquirer import prompt
from lib.cancamusa_common import random_guid
from lib.disguise.mac_vendors import get_mac_list, random_mac_for_vendor, search_wildcard_vendor
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