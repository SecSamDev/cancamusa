from script_iso import ScriptIsoBuilder
import os
from cancamusa_host import HostInfo
import bios_cloner
from configuration import CancamusaConfiguration
from script_iso import ScriptIsoBuilder
from jinja2 import Template
import subprocess
import ipaddress
import cancamusa_common
from rol_selector import generate_rol_files_for_host, ROLE_DNS, ROLE_DOMAIN_CONTROLLER

class WindowsHostBuilder:
    def __init__(self, project):
        project_path = project.config_path
        self.project = project
        self.project_path = os.path.join(project_path, "build")
        if not os.path.exists(self.project_path):
            os.mkdir(self.project_path)
        self.configuration = CancamusaConfiguration.load_or_create(None)
        self.seabios_path = None

    
    def build_net_interfaces(self):
        vmbrX = self.configuration.start_vmbr
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
        # TODO: Generate templates
        # TODO: copy scripts
        # TODO: create floppy ISO

        self.build_qemu_template(host)
        self.build_extra_iso(host)

        print(self.project_path)
        host_path = os.path.join(self.project_path, host.computer_name)
        if not os.path.exists(host_path):
            os.mkdir(host_path)
        if not os.path.exists(os.path.join(host_path, "bios.bin")) or ('CLEAN_ISOS' in os.environ and os.environ['CLEAN_ISOS'] == 'True'):
            if not self.seabios_path:
                self.seabios_path = bios_cloner.download_seabios()
            bios_cloner.compile_cloned_bios(host.bios, os.path.join(
                host_path, "bios.bin"), SEABIOS_PATH=self.seabios_path)

    def build_qemu_template(self, host):
        host_path = os.path.join(self.project_path, host.computer_name)
        if not os.path.exists(host_path):
            os.mkdir(host_path)

        qemu_template_file = os.path.join(
            host_path, str(host.host_id) + ".conf")
        with open(qemu_template_file, 'w') as qemu_template:
            compatible_win_image = self.configuration.select_win_image(
                host, 'CANCAMUSA_DEBUG' in os.environ,False)
            qemu_template.write('bootdisk: ide0\n')
            # Custom CPU with QEMU flags that hides virtualization
            qemu_template.write('cpu: custom-Cancamusa\n')
            qemu_template.write('vcpus: {}\n'.format(host.cpus[0].threads))
            qemu_template.write('cores: {}\n'.format(host.cpus[0].cores))
            qemu_template.write('sockets: {}\n'.format(str(len(host.cpus))))
            qemu_template.write('memory: {}\n'.format(host.ram.to_mib()))
            qemu_template.write('name: {}\n'.format(
                host.computer_name.replace("-", "").replace("_", "")))
            net_i = 0
            bridge_i = self.configuration.start_vmbr
            for hnet in host.networks:
                qemu_template.write(
                    'net{}: rtl8139={},bridge=vmbr{},firewall=1\n'.format(net_i, hnet.mac_address,bridge_i))
                net_i = net_i + 1
                bridge_i = bridge_i + 1
            qemu_template.write('numa: 0\n')
            qemu_template.write(
                'ostype: {}\n'.format("win"+str(host.os.major)))

            dcisc_i = 0
            for hnet in host.disks:
                # ide0:106/vm-106-disk-0.qcow2,size=128G
                qemu_template.write('ide{}: {}:{}/vm-{}-disk-{}.qcow2,size={}\n'.format(
                    dcisc_i, self.configuration.proxmox_image_storage, host.host_id, host.host_id, dcisc_i, hnet.size))
                storage_path = [x for x in self.configuration.proxmox_storages if x['name']
                                == self.configuration.proxmox_image_storage][0]['path']
                #qemu_disk_qcow2("{}/images/{}/vm-{}-disk-{}.qcow2".format(storage_path,host.host_id,host.host_id,dcisc_i), hnet.size)
                dcisc_i = dcisc_i + 1
            qemu_template.write("ide{}: {}:iso/{},media=cdrom\n".format(
                dcisc_i, self.configuration.proxmox_iso_storage, os.path.basename(compatible_win_image["path"])))
            dcisc_i = dcisc_i + 1
            qemu_template.write('scsihw: virtio-scsi-pci\n')
            
            bootsplash = os.path.join(self.project_path,'..','bootsplash.bmp')
            qemu_template.write(
                'args:-bios {} -boot menu=on,once=d,order=c,strict=on,splash={} -fda {} -smbios type=1,manufacturer=DELL,product="XPS 13 9360",version=2.6.2,serial=HB3O4WM,uuid=a80a97c5-e5a0-41ef-b8d2-00689114933a\n'.format(os.path.join(host_path, "bios.bin"),bootsplash, os.path.join(host_path, str(host.host_id) + ".img")))
            qemu_template.write("vmstatestorage: {}\n".format(self.configuration.proxmox_image_storage))
        print('QEMU template for proxmox created: ' + qemu_template_file)

    def build_extra_iso(self, host):
        builder = ScriptIsoBuilder(host, [], [])
        host_path = os.path.join(self.project_path, host.computer_name)
        
        if not os.path.exists(os.path.join(host_path,'iso_file')):
            os.mkdir(os.path.join(host_path,'iso_file'))
        
        # Build Autounattend --------------------------------------------------------
        compatible_win_image = self.configuration.select_win_image(
            host, 'CANCAMUSA_DEBUG' in os.environ,True,'CLEAN_ISOS' in os.environ)
        
        # Copy all scripts and configs that are not templates into the ISO file
        for (dirpath, dirnames, filenames) in os.walk(os.path.join(os.path.dirname(__file__), 'scripter', 'scripts', compatible_win_image['win_type'])):
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

        with open(os.path.join(os.path.dirname(__file__), 'scripter', 'templates', compatible_win_image['win_type'], 'Autounattend.xml.jinja'), 'r') as file_r:
            template = Template(file_r.read())
            lang = {
                'principal': host.language,
                'fall': 'en-EN'
            }
            win_image = {
                'image': compatible_win_image['selected_img'] + 1 #Index starts at one
            }
            host.selected_img_idx = compatible_win_image['selected_img']
            host.selected_img_pth = compatible_win_image["path"]
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

            with open(os.path.join(host_path,'iso_file', 'Autounattend.xml'), 'w') as file_w:
                file_w.write(template.render(lang=lang, principal_disk=principal_disk, disk_list=disk_list,
                                             computer_name=host.computer_name, principal_user=principal_user, win_image=win_image))

            builder.add_config(os.path.join(host_path,'iso_file', 'Autounattend.xml'))

        # Setup Network ----------------------------------------------------
        # O = Nombre de Adaptador, 2 = Direccion Fisica
        #"$headers = (getmac /fo csv /v | Select-Object -First 1).replace('\"','').split(',')"

        with open(os.path.join(os.path.dirname(__file__), 'scripter', 'templates', compatible_win_image['win_type'], 'setup-net.ps1.jinja'), 'r') as file_r:
            template = Template(file_r.read())
            actual_file_out_path = os.path.join(host_path,'iso_file', 'setup-net.ps1')
            with open(actual_file_out_path, 'w') as file_w:
                file_w.write(template.render(networks=host.networks))
            builder.add_script(actual_file_out_path)

        # Setup Socks Proxy ------------------------------------------------
        if 'proxy' in self.project.config:
            with open(os.path.join(os.path.dirname(__file__), 'scripter', 'templates', compatible_win_image['win_type'], 'set-proxy.bat.jinja'), 'r') as file_r:
                template = Template(file_r.read())
                actual_file_out_path = os.path.join(host_path,'iso_file', 'set-proxy.bat')
                with open(actual_file_out_path, 'w') as file_w:
                    file_w.write(template.render(proxy=self.project.config['proxy']))
                builder.add_script(actual_file_out_path)

        # Join Domain ------------------------------------------------------
        actual_domain = self.project.domain.get_domain(host.domain)
        if actual_domain == None:
            print("No domain configuration for: {}".format(host.domain))
        if len(self.project.domain.domains) > 0 and actual_domain and not ROLE_DOMAIN_CONTROLLER in host.roles.roles:
            # TODO: Improve Join Domain for multiple DomainControllers
            with open(os.path.join(os.path.dirname(__file__), 'scripter', 'templates', compatible_win_image['win_type'], 'join-domain.ps1.jinja'), 'r') as file_r:
                template = Template(file_r.read())
                actual_file_out_path = os.path.join(host_path,'iso_file', 'join-domain.ps1')
                with open(actual_file_out_path, 'w') as file_w:
                    acc = host.get_account_for_domain(host.domain)
                    if acc == None:
                        username = actual_domain.default_admin
                        password = actual_domain.default_admin_password
                    else:
                        username = acc.name
                        password = acc.password

                    file_w.write(template.render(domain_dc_ip=actual_domain.dc_ip,username=username,password=password,domain_name=actual_domain.domain))
                builder.add_script(actual_file_out_path)

        # Install sysmon ----------------------------------------------------
        if 'sysmon' in self.project.config:
            # If imported, download the sysmon config
            self.project.get_sysmon_file_if_not_exists()
            sysmon_conf = cancamusa_common.SYSMON_CONFIG_FILE
            sysmon_drv = self.project.config['sysmon']['driver']
            sysmon_srv = self.project.config['sysmon']['service']
            sysmon_alt = self.project.config['sysmon']['altitude']
            with open(os.path.join(os.path.dirname(__file__), 'scripter', 'templates', compatible_win_image['win_type'], 'install-sysmon.bat.jinja'), 'r') as file_r:
                template = Template(file_r.read())
                actual_file_out_path = os.path.join(host_path,'iso_file', 'install-sysmon.bat')
                with open(actual_file_out_path, 'w') as file_w:
                    file_w.write(template.render(sysmon_conf=sysmon_conf,sysmon_drv=sysmon_drv,sysmon_alt=sysmon_alt,sysmon_srv=sysmon_srv))
                builder.add_script(actual_file_out_path)

            actual_file_out_path = os.path.join(host_path, 'iso_file', sysmon_conf)
            with open(os.path.join('config_files', cancamusa_common.SYSMON_CONFIG_FILE),'r') as file_r:
                with open(actual_file_out_path,'w') as file_w:
                    file_w.write(file_r.read())
            builder.add_config(actual_file_out_path)

        # Install Winlogbeat ------------------------------------------------
        # TODO: hide winlogbeat
        # https://artifacts.elastic.co/downloads/beats/winlogbeat/winlogbeat-7.14.1-windows-x86_64.zip

        if 'winlogbeat' in self.project.config:
            # If imported, download the winlogbeat config
            self.project.get_winlogbeat_file_if_not_exists()
            with open(os.path.join(os.path.dirname(__file__), 'scripter', 'templates', compatible_win_image['win_type'], 'install-winlogbeat.bat.jinja'), 'r') as file_r:
                template = Template(file_r.read())
                actual_file_out_path = os.path.join(host_path,'iso_file', 'install-winlogbeat.bat')
                with open(actual_file_out_path, 'w') as file_w:
                    file_w.write(template.render(winlogbeat_config=cancamusa_common.WINLOGBEAT_CONFIG_FILE))
                builder.add_script(actual_file_out_path)

            actual_file_out_path = os.path.join(host_path, 'iso_file', cancamusa_common.WINLOGBEAT_CONFIG_FILE)
            with open(os.path.join('config_files', cancamusa_common.WINLOGBEAT_CONFIG_FILE),'r') as file_r:
                with open(actual_file_out_path,'w') as file_w:
                    file_w.write(file_r.read())
            builder.add_config(actual_file_out_path)

        # Deception options --------------------------------------------------
        with open(os.path.join(os.path.dirname(__file__), 'scripter', 'templates', compatible_win_image['win_type'], 'deception.bat.jinja'), 'r') as file_r:
            template = Template(file_r.read())
            actual_file_out_path = os.path.join(host_path,'iso_file', 'deception.bat')
            with open(actual_file_out_path, 'w') as file_w:
                file_w.write(template.render(cpus=host.cpus))
            builder.add_script(actual_file_out_path)

        # KMS Server ---------------------------------------------------------
        kms_server = self.project.primary_kms_config()
        if kms_server == None and actual_domain:
            kms_server = actual_domain.kms_server
        else:
            kms_server = "{}:1688".format(kms_server['ip'])
        if kms_server:
            with open(os.path.join(os.path.dirname(__file__), 'scripter', 'templates', compatible_win_image['win_type'], 'setup-kms.bat.jinja'), 'r') as file_r:
                template = Template(file_r.read())
                actual_file_out_path = os.path.join(host_path,'iso_file', 'setup-kms.bat')
                with open(actual_file_out_path, 'w') as file_w:
                    file_w.write(template.render(kms_server=kms_server))
                builder.add_script(actual_file_out_path)

        
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
