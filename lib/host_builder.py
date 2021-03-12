from script_iso import ScriptIsoBuilder
import os
from cancamusa_host import HostInfo
import bios_cloner
from configuration import CancamusaConfiguration

class WindowsHostBuilder:
    def __init__(self, project):
        project_path = project.config_path
        self.project = project
        self.project_path = os.path.join(project_path,"build")
        if not os.path.exists(self.project_path):
            os.mkdir(self.project_path)
        self.configuration = CancamusaConfiguration.load_or_create(None)
        self.seabios_path = None

    def build_host_image(self, host):
        """Build host scripts and templates

        Args:
            host HostInfo: Object that stores all host configuration
        """
        #TODO: Generate templates
        #TODO: copy scripts
        #TODO: create floppy ISO

        self.build_qemu_template(host)

        if not self.seabios_path:
            self.seabios_path = bios_cloner.download_seabios()
        print(self.project_path)
        host_path = os.path.join(self.project_path,host.computer_name)
        if not os.path.exists(host_path):
            os.mkdir(host_path)
        bios_cloner.compile_cloned_bios(host.bios, os.path.join(host_path,"bios.bin"),SEABIOS_PATH=self.seabios_path)
        


    def build_qemu_template(self, host):
        host_path = os.path.join(self.project_path,host.computer_name)
        if not os.path.exists(host_path):
            os.mkdir(host_path)
        
        qemu_template_file = os.path.join(host_path, str(host.host_id) + ".conf")
        with open(qemu_template_file, 'w') as qemu_template:
            compatible_win_image = self.configuration.select_win_image(host,'CANCAMUSA_DEBUG' in os.environ)
            qemu_template.write("ide0: {}:iso/{},media=cdrom\n".format(self.configuration.proxmox_iso_storage,os.path.basename(compatible_win_image["path"]) ))
            qemu_template.write('bootdisk: virtio0\n')
            qemu_template.write('vcpus: {}\n'.format(host.cpus[0].threads))
            qemu_template.write('cores: {}\n'.format(host.cpus[0].cores))
            qemu_template.write('sockets: {}\n'.format(str(len(host.cpus))))
            qemu_template.write('memory: {}\n'.format(8))
            qemu_template.write("ide1: {}:iso/{},media=cdrom\n".format(self.configuration.proxmox_iso_extra_storage,str(host.host_id) + ".iso"))
            qemu_template.write('name: {}\n'.format(host.computer_name.replace("-","").replace("_","")))
            net_i = 0
            for hnet in host.networks:
                qemu_template.write('net{}: virtio={},bridge=vmbr0,firewall=1\n'.format(net_i,hnet.mac_address))
                net_i = net_i + 1
            qemu_template.write('numa: 0\n')
            qemu_template.write('ostype: {}\n'.format("win"+str(host.os.major)))

            dcisc_i = 0
            for hnet in host.disks:
                #scsi1:106/vm-106-disk-0.qcow2,size=128G
                qemu_template.write('virtio{}:{}/vm-{}-disk-{}.qcow2,size={}\n'.format(dcisc_i, self.configuration.proxmox_image_storage,host.host_id,dcisc_i,hnet.size))
                qemu_disk_qcow2("/{}/images/{}/vm-{}-disk-{}.qcow2".format(self.configuration.proxmox_image_storage,host.host_id,host.host_id,dcisc_i), hnet.size)
                dcisc_i = dcisc_i + 1
            qemu_template.write('scsihw: virtio-scsi-pci\n')
            qemu_template_file.write('args:-bios {}\n'.format(os.path.join(host_path,"bios.bin")))
        print('QEMU template for proxmox created: ' + qemu_template_file)


def qemu_disk_qcow2(pth,size):
    if 'CANCAMUSA_DEBUG' in os.environ:
        return
    parent = os.path.dirname(pth)
    if not os.path.exists(parent):
        os.mkdir(parent)
    process = subprocess.Popen(["qemu-img","create","-f","qcow2",pth,size], stdout=subprocess.PIPE, cwd=SEABIOS_PATH)
    output, error = process.communicate()
    p_status = process.wait()
    process.terminate()
    