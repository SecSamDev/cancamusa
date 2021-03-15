from script_iso import ScriptIsoBuilder
import os
from cancamusa_host import HostInfo
import bios_cloner
from configuration import CancamusaConfiguration

class ProxmoxDeployer:
    def __init__(self, project):
        project_path = project.config_path
        self.project = project
        self.project_path = os.path.join(project_path,"build")
        if not os.path.exists(self.project_path):
            os.mkdir(self.project_path)
        self.configuration = CancamusaConfiguration.load_or_create(None)

    def deploy_host(self, host):
        host_path = os.path.join(self.project_path,host.computer_name)
        if not os.path.exists(host_path):
            return
        qemu_template_file = os.path.join(host_path, str(host.host_id) + ".conf")
        if not os.path.exists(qemu_template_file):
            return
        # Copy QEMU template
        with open(qemu_template_file, 'r') as file_r:
            with open(os.path.join(self.configuration.proxmox_templates, os.path.basename(qemu_template_file)), 'w') as file_w:
                file_w.write(file_r.read())
        
        dcisc_i = 0 
        # Create qcow2 images
        for hdisk in host.disks:
            qemu_disk_qcow2("/{}/images/{}/vm-{}-disk-{}.qcow2".format(self.configuration.proxmox_image_storage,host.host_id,host.host_id,dcisc_i), hdisk.size)
            dcisc_i = dcisc_i + 1
        
        


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
    