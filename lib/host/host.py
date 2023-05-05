import os
import codecs
import json

from PyInquirer import prompt

from lib.disguise.bios_database import BIOS_AMERICAN_MEGATREND_ALASKA_F5
from lib.host.accounts import HostInfoWindowsAccounts
from lib.host.bios import HostInfoBios
from lib.host.common import filter_service_account, size_textual_to_numeric
from lib.host.cpu import HostInfoCpu
from lib.host.disk import HostInfoDisk
from lib.host.network import HostInfoNetwork
from lib.host.oem import HostInfoOEM
from lib.host.ram import HostInfoRAM
from lib.host.roles import HostInfoRoles
from lib.host.windows import HostInfoWindowsVersion
from lib.host.programms import HostInfoPrograms

def read_host_information(pth):
    return HostInfo.host_info_from_directory(pth)

def read_host_files_in_path(pth):
    if not os.path.isdir(pth):
        raise Exception("Invalid host info path: " + pth)

    host_in_dir = os.listdir(pth)
    host_list = []
    for host_dir in host_in_dir:
        try:
            host_list.append(read_host_information(
                os.path.join(pth, host_dir)))
        except:
            print('Error reading host information for ' + host_dir)
    return host_list

class HostInfo:
    def __init__(self, host_id=1000, password_generator='CancamusaRocks123!',default_language="en-EN"):
        self.host_id = host_id
        self.disks = []
        self.bios = HostInfoBios(BIOS_AMERICAN_MEGATREND_ALASKA_F5)
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
        self.oem = HostInfoOEM()

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
        to_ret["oem"] = self.oem.to_json()
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
        if 'oem' in obj:
            host.oem = HostInfoOEM.from_json(obj["oem"])
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
                            'Resume', 'Name','OS Version', 'Disks','RAM','CPUs', 'Network interfaces', 'Language', 'Domain', 'Bios',  'Accounts', 'Roles', 'OEM', 'Back', 'Cancel']}])
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
            elif answer['option'] == 'OEM':
                self.oem.edit_interactive(project)
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