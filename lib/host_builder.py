from script_iso import ScriptIsoBuilder
import os

class WindowsHostBuilder:
    def __init__(self, project_path):
        self.project_path = os.path.join(project_path,"build")
        if not os.path.exists(self.project_path):
            os.mkdir(self.project_path)

    def build_host_image(self, host):
        #TODO: Generate templates
        #TODO: copy scripts
        #TODO: create floppy ISO
        print(self.project_path)
        pass