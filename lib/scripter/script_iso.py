try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

import pycdlib
import os
import tempfile
import subprocess

class ScriptIsoBuilder:
    """Allow to easily create custom ISOs with all the scripts and configuration files
        needed to build the full Windows Machine.
    """
    def __init__(self,host, scripts, configs):
        self.host = host
        self.scripts = []
        self.configs = set()
        for scr in scripts:
            self.scripts.add(scr)
        for cfg in configs:
            self.configs.add(cfg)

    
    def add_config(self, config_path):
        self.configs.add(config_path)

    def add_script(self,script_path):
        self.scripts.append(script_path)

    def init_script(self):
        script = ""
        for scr in self.scripts:
            scr = os.path.basename(scr)
            if scr.endswith("ps1"):
                script += 'Powershell.exe -executionpolicy remotesigned -File .\\' + scr + "\n"
            elif scr.endswith(".bat"):
                script += 'call .\\' + scr + "\n"
            elif scr.endswith(".py"):
                script += 'SET RUN_DOTPY=python.exe ' + scr + '\nset SCRIPT=\nIF EXIST "python.exe" (\n\tSET SCRIPT=%RUN_DOTPY%\n)\n%SCRIPT%'
        return bytearray(script, "utf8")

    def build_geniso(self, output_dir):
        # Added installation logs
        init_script = "@echo off\n>C:\\init\\install.log (\n" + self.init_script() + "\n)\n"
        tmp_dir = tempfile.mkdtemp()
        with open(os.path.join(tmp_dir, 'init_script.bat'), 'wb') as file_w:
            file_w.write(init_script)
        for scr in self.scripts:
            with open(scr,'rb') as file_r:
                with open(os.path.join(tmp_dir, os.path.basename(scr)), 'wb') as file_w:
                    file_w.write(file_r.read())
        for cfg in self.configs:
            with open(cfg,'rb') as file_r:
                with open(os.path.join(tmp_dir, os.path.basename(cfg)), 'wb') as file_w:
                    file_w.write(file_r.read())
        
        unmountCommand = 'genisoimage -o ' + output_dir + ' -J -R -l ' + str(tmp_dir)
        process = subprocess.Popen(unmountCommand.split(), stdout=subprocess.PIPE)
        out, err = process.communicate()
        p_status = process.wait()
        process.terminate()
        print(unmountCommand)
    
    def build_floppy(self, output_dir):
        if os.path.exists(output_dir):
            os.remove(output_dir)
        # Added installation logs
        init_script = "@echo off\n>C:\\init\\install.log (\n" + self.init_script() + "\n)\n"
        tmp_dir = tempfile.mkdtemp()
        command = 'mkfs.msdos -C ' + output_dir + ' 1440'
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        out, err = process.communicate()
        p_status = process.wait()
        process.terminate()
        command = 'mount -o loop ' + output_dir + ' ' + tmp_dir
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        out, err = process.communicate()
        p_status = process.wait()
        process.terminate()
        with open(os.path.join(tmp_dir, 'init_script.bat'), 'wb') as file_w:
            file_w.write(init_script)
        for scr in self.scripts:
            with open(scr,'rb') as file_r:
                with open(os.path.join(tmp_dir, os.path.basename(scr)), 'wb') as file_w:
                    file_w.write(file_r.read().replace(b"\r",b"").replace(b"\n",b"\r\n"))
        for cfg in self.configs:
            with open(cfg,'rb') as file_r:
                with open(os.path.join(tmp_dir, os.path.basename(cfg)), 'wb') as file_w:
                    file_w.write(file_r.read().replace(b"\r",b"").replace(b"\n",b"\r\n"))
        command = 'umount ' + tmp_dir
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        out, err = process.communicate()
        p_status = process.wait()
        process.terminate()
            

    def build(self,output_dir):
        """This builds a custom ISO for the selected machine with all scripts and configuration files needed

        Args:
            output_dir (string): Where to create the ISO file
        """
        iso = pycdlib.PyCdlib()
        iso.new(interchange_level=3,
            joliet=3,
            rock_ridge='1.09',
            vol_ident='cidata',
            sys_ident='LINUX')
        init_script = self.init_script()

        iso.add_fp(BytesIO(init_script), len(init_script),'/INIT.;1',rr_name="init_script.bat",joliet_path='init_script.bat')

        file_id = 1
        for scr in self.scripts:
            with open(scr,'rb') as file_r:
                content = file_r.read()
                iso.add_fp(BytesIO(content), len(content),iso_patth= '/F' + str(file_id) + '.;1',
                rr_name=os.path.basename(scr) ,joliet_path='/'+os.path.basename(scr))
            file_id = file_id + 1
        for cfg in self.configs:
            with open(cfg,'rb') as file_r:
                content = file_r.read()
                iso.add_fp(BytesIO(content), len(content),iso_patth= '/F' + str(file_id) + '.;1',
                rr_name=os.path.basename(cfg) ,joliet_path='/'+os.path.basename(cfg))
        iso.write(output_dir)
        # mkisofs -o /tmp/cd.iso /tmp/directory/
        iso.close()
