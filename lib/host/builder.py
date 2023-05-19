import os
import re
import subprocess
import ipaddress
import uuid
import base64
from os.path import expanduser
from jinja2 import Template

from lib.host.host import HostInfo
from lib.disguise.bios_cloner import download_seabios, compile_cloned_bios
from lib.configuration import CancamusaConfiguration
from lib.cancamusa_common import SYSMON_CONFIG_FILE, WINLOGBEAT_CONFIG_FILE
from lib.scripter.script_iso import ScriptIsoBuilder
from lib.scripter.rol_selector import generate_rol_files_for_host, ROLE_DNS, ROLE_DOMAIN_CONTROLLER
from lib.scripter.activator import select_license

class WindowsHostBuilder:
    def __init__(self, project):
        project_path = project.config_path
        self.project = project
        self.project_path = os.path.join(project_path, "build")
        if not os.path.exists(self.project_path):
            os.mkdir(self.project_path)
        self.configuration = CancamusaConfiguration.load_or_create(None)
        self.seabios_path = None

    def build_adm_scripts(self, hosts):
        print("Creating ADM scripts in: {}/*.sh".format(self.project_path))
        with open(os.path.join(self.project_path,'start_all.sh'),'w') as file_w:
            for host in hosts:
                file_w.write("qm start {}\n".format(host.host_id))

        with open(os.path.join(self.project_path,'stop_all.sh'),'w') as file_w:
            for host in hosts:
                file_w.write("qm stop {}\n".format(host.host_id))

    def build_net_interfaces(self):
        vmbrX = self.project.config["start_vmbr"]
        net_file = "# To be added in /etc/network/interfaces"
        for net in self.project.networks:
            net_file += """
auto vmbr{}
iface vmbr{} inet static
	address {}
	bridge-ports none
	bridge-stp off
	bridge-fd 0
	bridge-vlan-aware yes
	bridge-vids 2-4094
    #post-up iptables -t nat -A POSTROUTING -s '{}' -o eno1 -j MASQUERADE
	#post-down iptables -t nat -D POSTROUTING -s '{}' -o eno1 -j MASQUERADE

""".format(vmbrX,vmbrX,str(net),str(net),str(net))
            vmbrX = vmbrX + 1
        
        net_path = os.path.join(self.project_path,'net_interfaces')
        print("Creating network configuration in: {}".format(net_path))
        with open(net_path,'w') as file_w:
            file_w.write(net_file)


    def build_host_image(self, host):
        """Build host scripts and templates

        Args:
            host HostInfo: Object that stores all host configuration
        """

        self.build_qemu_template(host)
        self.build_extra_iso(host)

        host_path = os.path.join(self.project_path, host.computer_name)
        if not os.path.exists(host_path):
            os.mkdir(host_path)
        if not os.path.exists(os.path.join(host_path, "bios.bin")) or ('CLEAN_ISOS' in os.environ and os.environ['CLEAN_ISOS'] == 'True'):
            if not self.seabios_path:
                self.seabios_path = download_seabios()
            compile_cloned_bios(host.bios, os.path.join(host_path, "bios.bin"), SEABIOS_PATH=self.seabios_path)
        
    def build_qemu_template(self, host):
        host_path = os.path.join(self.project_path, host.computer_name)
        if not os.path.exists(host_path):
            os.mkdir(host_path)

        qemu_template_file = os.path.join(
            host_path, str(host.host_id) + ".conf")
        ark = host.cpus[0].architecture.upper()
        with open(qemu_template_file, 'w') as qemu_template:
            compatible_win_image = self.configuration.select_win_image(
                host, 'CANCAMUSA_DEBUG' in os.environ,False)
            qemu_template.write('bootdisk: ide0\n')
            # Custom CPU with QEMU flags that hides virtualization
            qemu_template.write('cpu: custom-Cancamusa{}\n'.format(ark))
            qemu_template.write('vcpus: {}\n'.format(host.cpus[0].threads))
            qemu_template.write('cores: {}\n'.format(host.cpus[0].cores))
            qemu_template.write('sockets: {}\n'.format(str(len(host.cpus))))
            qemu_template.write('memory: {}\n'.format(host.ram.to_mib()))
            qemu_template.write('name: {}\n'.format(
                host.computer_name.replace("-", "").replace("_", "")))
            net_i = 0
            bridge_i = self.project.config["start_vmbr"]
            for hnet in host.networks:
                qemu_template.write(
                    'net{}: rtl8139={},bridge=vmbr{},firewall=1\n'.format(net_i, hnet.mac_address,bridge_i))
                net_i = net_i + 1
                bridge_i = bridge_i + 1
            qemu_template.write('numa: 0\n')
            qemu_template.write(
                'ostype: {}\n'.format(get_win_os(host.os.win_type)))

            sata_i = 0
            for hnet in host.disks:
                # ide0:106/vm-106-disk-0.qcow2,size=128G
                qemu_template.write('sata{}: {}:{}/vm-{}-disk-{}.qcow2,size={}\n'.format(
                    sata_i, self.configuration.proxmox_image_storage, host.host_id, host.host_id, sata_i, hnet.size))
                storage_path = [x for x in self.configuration.proxmox_storages if x['name']
                                == self.configuration.proxmox_image_storage][0]['path']
                #qemu_disk_qcow2("{}/images/{}/vm-{}-disk-{}.qcow2".format(storage_path,host.host_id,host.host_id,dcisc_i), hnet.size)
                sata_i = sata_i + 1

            qemu_template.write("ide0: {}:iso/{},media=cdrom\n".format(
                self.configuration.proxmox_iso_storage, os.path.basename(compatible_win_image["path"])))
            
            qemu_template.write('scsihw: virtio-scsi-pci\n')
            
            # bootsplash = os.path.join(self.project_path,'..','bootsplash.bmp')

            ### ARGS smbios for proxmox not working in 6.4
            # BIOS
            # Note: base64=1 not working... we will use b64 to remove characters
            smbios = "-smbios type=0,vendor={},version={},date={},release={} ".format(smb(host.bios.manufacturer), smb(host.bios.smbios_major_version)+"."+smb(host.bios.smbios_minor_version), release_version(host.bios.release_date),bios_date(host.bios.release_date))
            # SYSTEM
            # smbios = smbios + "-smbios type=1,manufacturer={},product={},version={},serial={},uuid={},sku={},family={} ".format(smb("ASUS"), smb("All Series"), smb("System Version"),smb(uuid.uuid4()),smb(uuid.uuid4()),smb("All"),smb("ASUS MB"))
            # BaseBoard TODO: Extract info
            smbios = smbios + "-smbios type=2,manufacturer={},product={},version={},serial={} ".format(smb("ASUSTEK COMPUTER INC."), smb("TRX40"),smb("Rev 1.2"), smb(uuid.uuid4()))

            if host.os.win_type == 'win11':
                # TODO: Build custom OVMF bios
                qemu_template.write("bios: ovmf\n")
                qemu_template.write("machine: pc-q35-6.2\n")
                qemu_template.write("efidisk0: {}:{}/vm-{}-disk-{}.qcow2,efitype=4m,pre-enrolled-keys=1,size=528K \n".format(self.configuration.proxmox_image_storage, host.host_id, host.host_id, sata_i))
                sata_i = sata_i + 1
                # UEFI
                qemu_template.write(
                    'args: -boot menu=on,once=d,order=c,strict=on -fda {} {}\n'.format(os.path.join(host_path, str(host.host_id) + ".img"), smbios))
                qemu_template.write("tpmstate0: {}:{}/vm-{}-disk-{}.raw,size=4M,version=v2.0\n".format(self.configuration.proxmox_image_storage, host.host_id, host.host_id, sata_i))
                sata_i = sata_i + 1
            else:
                qemu_template.write(
                    'args:-bios {} -boot menu=on,once=d,order=c,strict=on -fda {} {}\n'.format(os.path.join(host_path, "bios.bin"), os.path.join(host_path, str(host.host_id) + ".img"), smbios))
            qemu_template.write("vmstatestorage: {}\n".format(self.configuration.proxmox_image_storage))

            # smbios1 = System Information https://en.wikipedia.org/wiki/System_Management_BIOS
            qemu_template.write("smbios1: uuid={},manufacturer={},product={},version={},serial={},sku={},family={},base64=1 \n".format(uuid.uuid4(), b64("ASUS"), b64("All Series"), b64("System Version"),b64(uuid.uuid4()),b64("All"),b64("ASUS MB")))

            
        print('QEMU template for proxmox created: ' + qemu_template_file)

    def build_extra_iso(self, host):
        builder = ScriptIsoBuilder(host,self.project_path, [], [])
        host_path = os.path.join(self.project_path, host.computer_name)
        
        if not os.path.exists(os.path.join(host_path,'iso_file')):
            os.mkdir(os.path.join(host_path,'iso_file'))
        
        
        # Build Autounattend --------------------------------------------------------
        compatible_win_image = self.configuration.select_win_image(
            host, 'CANCAMUSA_DEBUG' in os.environ,True,'CLEAN_ISOS' in os.environ)
        
        # Copy all scripts and configs that are not templates into the ISO file
        for (dirpath, dirnames, filenames) in os.walk(os.path.join(os.path.dirname(__file__),'..', 'scripter', 'scripts', compatible_win_image['win_type'])):
            for file in filenames:
                # This scripts must not be added to the initial execution script
                builder.add_config(os.path.join(dirpath, file))

        # Use extra files to load files and directoris into the floppy disk
        if os.path.exists(os.path.join(host_path,'extra_files')):
            for (dirpath, dirnames, filenames) in os.walk(os.path.join(host_path,'extra_files')):
                for file in filenames:
                    # This scripts must not be added to the initial execution script
                    builder.add_config(os.path.join(dirpath, file))
                for dir in dirnames:
                    builder.add_folder(os.path.join(dirpath, dir))

        file_path = os.path.join(host_path,'iso_file', 'Autounattend.xml')
        if not os.path.exists(file_path):
            with open(os.path.join(os.path.dirname(__file__), '..', 'scripter', 'templates', compatible_win_image['win_type'], 'Autounattend.xml.jinja'), 'r') as file_r:
                template = Template(file_r.read())
                lang = {
                    'principal': host.language,
                    'fall': 'en-EN'
                }
                win_image = {
                    'image': compatible_win_image['selected_img'] + 1, #Index starts at one
                    'name' : compatible_win_image['images'][str(compatible_win_image['selected_img'] + 1)]
                }
                host.selected_img_idx = compatible_win_image['selected_img']
                host.selected_img_md5 = compatible_win_image["md5"]
                principal_disk = None
                disk_list = []
                for disk in host.disks:
                    if disk.device_id == 'C':
                        principal_disk = disk
                    else:
                        disk_list.append(disk)

                host_domain = None
                principal_user = None
                if host.domain:
                    domains = list(
                        map(lambda x: x.domain, self.project.domain.domains))
                    host_domain_pos = domains.index(host.domain)
                    host_domain = self.project.domain.domains[host_domain_pos]
                    
                
                if not host_domain:
                    if len(host.accounts) > 0:
                        principal_user = {
                            'name': host.accounts[0].name,
                            'password': host.accounts[0].password,
                            'group': 'Administrators',
                            'organization': host.computer_name
                        }
                    else:
                        principal_user = {
                            'name': 'Administrator',
                            'password': "Cancamusa123Rocks!",
                            'group': 'Administrators',
                            'organization': host.computer_name
                        }
                else:
                    # Account of valid domain
                    if len(host.accounts) > 0:
                        for acc in host.accounts:
                            if acc.domain == host_domain.name:
                                principal_user = {
                                    'name': acc.name,
                                    'password': acc.password,
                                    'group': 'Administrators',
                                    'organization': host.computer_name
                                }
                            break
                    if principal_user == None:
                        # Last resource => use domain account
                        principal_user = {
                            'name': host_domain.default_admin,
                            'password': host_domain.default_admin_password,
                            'group': 'Administrators',
                            'organization': host.computer_name #Still not in domain
                        }

                with open(file_path, 'w') as file_w:
                    file_w.write(template.render(lang=lang, principal_disk=principal_disk, disk_list=disk_list,
                                                computer_name=host.computer_name, principal_user=principal_user, win_image=win_image))

        builder.add_config(file_path)

        # Setup Network ----------------------------------------------------
        # O = Nombre de Adaptador, 2 = Direccion Fisica
        #"$headers = (getmac /fo csv /v | Select-Object -First 1).replace('\"','').split(',')"

        file_path = os.path.join(host_path,'iso_file', 'setup-net.ps1')
        actual_domain = self.project.domain.get_domain(host.domain)
        if not os.path.exists(file_path):
            with open(os.path.join(os.path.dirname(__file__), '..', 'scripter', 'templates', compatible_win_image['win_type'], 'setup-net.ps1.jinja'), 'r') as file_r:
                template = Template(file_r.read())
                dc_server = self.project.primary_dc_config()
                dc_ip = dc_server['ip'] if not dc_server['ip'] else dc_server['ip']
                if dc_ip:
                    dc_ip = ipaddress.ip_address(dc_ip)
                    for netw in host.networks:
                        if dc_ip in ipaddress.ip_network("{}/{}".format(netw.ip_address[0], netw.ip_subnet[0]), False):
                            netw.dns_servers[0] = str(dc_ip)

                with open(file_path, 'w') as file_w:
                    file_w.write(template.render(networks=host.networks))
        builder.add_script(file_path)

        # Setup Socks Proxy ------------------------------------------------
        
        if 'proxy' in self.project.config:
            file_path = os.path.join(host_path,'iso_file', 'set-proxy.bat')
            if not os.path.exists(file_path):
                with open(os.path.join(os.path.dirname(__file__), '..', 'scripter', 'templates', compatible_win_image['win_type'], 'set-proxy.bat.jinja'), 'r') as file_r:
                    template = Template(file_r.read())
                    with open(file_path, 'w') as file_w:
                        file_w.write(template.render(proxy=self.project.config['proxy']))
            builder.add_script(file_path)

        # Join Domain ------------------------------------------------------
        if actual_domain == None:
            print("No domain configuration for: {}".format(host.domain))
        if len(self.project.domain.domains) > 0 and actual_domain and not ROLE_DOMAIN_CONTROLLER in host.roles.roles:
            file_path = os.path.join(host_path,'iso_file', 'join-domain.ps1')
            if not os.path.exists(file_path):
                # TODO: Improve Join Domain for multiple DomainControllers
                with open(os.path.join(os.path.dirname(__file__), '..', 'scripter', 'templates', compatible_win_image['win_type'], 'join-domain.ps1.jinja'), 'r') as file_r:
                    template = Template(file_r.read())
                    
                    with open(file_path, 'w') as file_w:
                        acc = host.get_account_for_domain(host.domain)
                        if acc == None:
                            username = actual_domain.default_admin
                            password = actual_domain.default_admin_password
                        else:
                            # Use domain account, not the local one
                            acc = actual_domain.get_user(acc.name)
                            username = acc['account_name']
                            password = acc['password']

                        file_w.write(template.render(domain_dc_ip=actual_domain.dc_ip,username=username,password=password,domain_name=actual_domain.domain))
            builder.add_script(file_path)

        # Install sysmon ----------------------------------------------------
        if 'sysmon' in self.project.config:
            # If imported, download the sysmon config
            self.project.get_sysmon_file_if_not_exists()
            sysmon_conf = SYSMON_CONFIG_FILE
            sysmon_drv = self.project.config['sysmon']['driver']
            sysmon_srv = self.project.config['sysmon']['service']
            sysmon_alt = self.project.config['sysmon']['altitude']
            sysmon_url = self.project.config['sysmon']['download']
            with open(os.path.join(os.path.dirname(__file__), '..', 'scripter', 'templates', compatible_win_image['win_type'], 'install-sysmon.bat.jinja'), 'r') as file_r:
                template = Template(file_r.read())
                actual_file_out_path = os.path.join(host_path,'iso_file', 'install-sysmon.bat')
                with open(actual_file_out_path, 'w') as file_w:
                    file_w.write(template.render(sysmon_conf=sysmon_conf,sysmon_drv=sysmon_drv,sysmon_alt=sysmon_alt,sysmon_srv=sysmon_srv, sysmon_url=sysmon_url))
                builder.add_script(actual_file_out_path)

            actual_file_out_path = os.path.join(host_path, 'iso_file', sysmon_conf)
            with open(os.path.join('config_files', SYSMON_CONFIG_FILE),'r') as file_r:
                with open(actual_file_out_path,'w') as file_w:
                    file_w.write(file_r.read())
            builder.add_config(actual_file_out_path)

        # Install Winlogbeat ------------------------------------------------
        # TODO: hide winlogbeat
        # https://artifacts.elastic.co/downloads/beats/winlogbeat/winlogbeat-7.14.1-windows-x86_64.zip

        if 'winlogbeat' in self.project.config:
            # If imported, download the winlogbeat config
            self.project.get_winlogbeat_file_if_not_exists()
            with open(os.path.join(os.path.dirname(__file__), '..', 'scripter', 'templates', compatible_win_image['win_type'], 'install-winlogbeat.bat.jinja'), 'r') as file_r:
                template = Template(file_r.read())
                actual_file_out_path = os.path.join(host_path,'iso_file', 'install-winlogbeat.bat')
                with open(actual_file_out_path, 'w') as file_w:
                    file_w.write(template.render(winlogbeat_config=WINLOGBEAT_CONFIG_FILE,winlogbeat_url=self.project.config['winlogbeat']['download']))
                builder.add_script(actual_file_out_path)

            actual_file_out_path = os.path.join(host_path, 'iso_file', WINLOGBEAT_CONFIG_FILE)
            with open(os.path.join('config_files', WINLOGBEAT_CONFIG_FILE),'r') as file_r:
                with open(actual_file_out_path,'w') as file_w:
                    file_w.write(file_r.read())
            builder.add_config(actual_file_out_path)

        # Deception options --------------------------------------------------
        file_path = os.path.join(host_path,'iso_file', 'deception.bat')
        if not os.path.exists(file_path):
            with open(os.path.join(os.path.dirname(__file__), '..', 'scripter', 'templates', compatible_win_image['win_type'], 'deception.bat.jinja'), 'r') as file_r:
                template = Template(file_r.read())
                with open(file_path, 'w') as file_w:
                    file_w.write(template.render(cpus=host.cpus, bios=host.bios))
        builder.add_script(file_path)

        # KMS Server ---------------------------------------------------------

        kms_server = self.project.primary_kms_config()
        if kms_server == None and actual_domain:
            kms_server = actual_domain.kms_server
        else:
            kms_server = "{}:1688".format(kms_server['ip'])
            
        if kms_server:
            file_path = os.path.join(host_path,'iso_file', 'setup-kms.ps1')
            if not os.path.exists(file_path):
                product_key = select_license(compatible_win_image["images"][str(int(host.selected_img_idx) + 1)])
                with open(os.path.join(os.path.dirname(__file__), '..', 'scripter', 'templates', compatible_win_image['win_type'], 'setup-kms.ps1.jinja'), 'r') as file_r:
                    template = Template(file_r.read())
                    with open(file_path, 'w') as file_w:
                        file_w.write(template.render(kms_server=kms_server, product_key=product_key))
            builder.add_script(file_path)

        if 'ssh' in self.project.config and self.project.config['ssh']:
            try:
                # SSH not supported for Win7/Win8.1/2008/2012/2016
                ssh_path = os.path.join(os.path.dirname(__file__), '..', 'scripter', 'scripts', compatible_win_image['win_type'], 'install-sshd.ps1')
                if self.project.config['ssh']['enabled'] and os.path.exists(ssh_path):
                    builder.add_script(ssh_path)
                    # Enable SSH
                    if self.project.config['ssh']['copy_public_key']:
                        public_rsa_key_location = os.path.join(expanduser("~"),".ssh","id_rsa.pub")
                        actual_file_out_path = os.path.join(host_path,'iso_file', 'authorized_keys')
                        if not os.path.exists(actual_file_out_path):
                            with open(public_rsa_key_location, 'rb') as file_r:
                                with open(actual_file_out_path, 'wb') as file_w:
                                    file_w.write(file_r.read())
                        builder.add_config(actual_file_out_path)
            except:
                pass
                
        # Extra scripts in the same batch of scripts
        builder.add_scripts([
            # Set Powershell profile
            os.path.join(os.path.dirname(__file__),'..', 'scripter', 'scripts', compatible_win_image['win_type'], 'set-profile.ps1')
        ])
        
        # Build Windows ROLES -> Last to be executed (reboots needed) and need to be in domain
        generate_rol_files_for_host(host,builder,self.project)

        # BUILD Floppy
        extra_iso_path = os.path.join(host_path, str(host.host_id) + ".img")
        builder.build_floppy(extra_iso_path)


def qemu_disk_qcow2(pth, size):
    # DEBUG mode = Not a Proxmox env
    if 'CANCAMUSA_DEBUG' in os.environ:
        return
    parent = os.path.dirname(pth)
    if not os.path.exists(parent):
        os.mkdir(parent)
    process = subprocess.Popen(
        ["qemu-img", "create", "-f", "qcow2", pth, str(size)], stdout=subprocess.PIPE)
    output, error = process.communicate()
    p_status = process.wait()
    process.terminate()

def smb(txt):
    txt = str(txt).replace(".","").replace(",","").replace(" - "," ").replace(" -"," ").replace(" ","")
    #message_bytes = txt.encode('ascii')
    #return str(base64.b64encode(message_bytes).decode('ascii'))
    return txt

def b64(txt):
    message_bytes = str(txt).encode('ascii')
    return str(base64.b64encode(message_bytes).decode('ascii'))

def release_version(txt):
    mtc = re.search(r"([0-9]{8})[0-9]{6}\.[0-9]{6}\+[0-9]{3}", txt)
    if mtc:
        date = mtc.group(1)
        return "{}/{}/{}".format(date[6:8], date[4:6], date[0:4])
        
    else:
        "07/06/2019"

def bios_date(txt):
    mtc = re.search(r"([0-9]{8})[0-9]{6}\.[0-9]{6}\+[0-9]{3}", txt)
    if mtc:
        date = mtc.group(1)
        return "{}.{}".format(date[4:6], date[2:4])
        
    else:
        "06.19"

def get_win_os(hos):
    if hos in ["win7", "win2008r2"]:
        return "win7"
    if hos in ["win10", "win2016", "win2019"]:
        return "win10"
    if hos in ["win11", "win2022"]:
        return "win11"
    if hos in ["win81", "win2012r2"]:
        return "win8"
    return "win7"

