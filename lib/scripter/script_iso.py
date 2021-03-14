try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

import pycdlib
import os


class ScriptIsoBuilder:
    """Allow to easily create custom ISOs with all the scripts and configuration files
        needed to build the full Windows Machine.
    """
    def __init__(self,host, scripts, configs):
        self.host = host
        self.scripts = set()
        self.configs = set()
        for scr in scripts:
            self.scripts.add(scr)
        for cfg in configs:
            self.configs.add(cfg)

    
    def add_config(self, config_path):
        self.configs.add(config_path)

    def add_script(self,script_path):
        self.scripts.add(script_path)

    def init_script(self):
        script = b""
        for scr in self.scripts:
            scr = os.path.basename(scr)
            if scr.endswith("ps1"):
                script += b'Powershell.exe -executionpolicy remotesigned -File .\\' + scr + "\n"
            elif scr.endswith(".bat"):
                script += b'call .\\' + scr + "\n"
            elif scr.endswith(".py"):
                script += b'SET RUN_DOTPY=python.exe ' + scr + '\nset SCRIPT=\nIF EXIST "python.exe" (\n\tSET SCRIPT=%RUN_DOTPY%\n)\n%SCRIPT%'
        return script
            

    def build(self,output_dir):
        """This builds a custom ISO for the selected machine with all scripts and configuration files needed

        Args:
            output_dir (string): Where to create the ISO file
        """
        iso = pycdlib.PyCdlib()
        iso.new(interchange_level=3)
        init_script = self.init_script()
        iso.add_fp(BytesIO(init_script), len(init_script), '/init_script.bat.;1')

        for scr in self.scripts:
            with open(scr,'rb') as file_r:
                content = file_r.read()
                iso.add_fp(BytesIO(content), len(content),'/'+os.path.basename(scr)+'.;1')

        for cfg in self.configs:
            with open(cfg,'rb') as file_r:
                content = file_r.read()
                iso.add_fp(BytesIO(content), len(content),'/'+os.path.basename(cfg)+'.;1')
        
        iso.write(os.path.join(output_dir, self.host.host_id + ".iso"))
        iso.close()
