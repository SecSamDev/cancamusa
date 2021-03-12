from script_iso import ScriptIsoBuilder
import os
from cancamusa_host import HostInfo
import bios_cloner

class WindowsHostBuilder:
    def __init__(self, project):
        project_path = project.config_path
        self.project = project
        self.project_path = os.path.join(project_path,"build")
        if not os.path.exists(self.project_path):
            os.mkdir(self.project_path)
        
        self.seabios_path = None

    def build_host_image(self, host):
        """Build host scripts and templates

        Args:
            host HostInfo: Object that stores all host configuration
        """
        #TODO: Generate templates
        #TODO: copy scripts
        #TODO: create floppy ISO

        if not self.seabios_path:
            self.seabios_path = bios_cloner.download_seabios()
        print(self.project_path)
        host_path = os.path.join(self.project_path,host.computer_name)
        if not os.path.exists(host_path):
            os.mkdir(host_path)
        bios_cloner.compile_cloned_bios(host.bios, os.path.join(host_path,"bios.bin"),SEABIOS_PATH=self.seabios_path)
        pass