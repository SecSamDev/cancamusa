from script_iso import ScriptIsoBuilder
import os
from cancamusa_host import HostInfo

class WindowsHostBuilder:
    def __init__(self, project_path):
        self.project_path = os.path.join(project_path,"build")
        if not os.path.exists(self.project_path):
            os.mkdir(self.project_path)

    def build_host_image(self, host):
        """Build host scripts and templates

        Args:
            host (HostInfo): Object that stores all host configuration
        """
        #TODO: Generate templates
        #TODO: copy scripts
        #TODO: create floppy ISO
        print(self.project_path)
        pass