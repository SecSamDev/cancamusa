try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

import pycdlib
import os
import tempfile
import subprocess
from distutils.dir_util import copy_tree

class ScriptIsoBuilder:
    """Allow to easily create custom ISOs with all the scripts and configuration files
        needed to build the full Windows Machine.
    """
    def __init__(self, host, project_path, scripts, configs):
        self.project_path = project_path
        self.host = host
        self.scripts = []
        self.folders = []
        self.configs = set()
        for scr in scripts:
            self.scripts.add(scr)
        for cfg in configs:
            self.configs.add(cfg)

    
    def add_config(self, config_path):
        self.configs.add(os.path.abspath(config_path))

    def add_scripts(self,script_path):
        new_scripts = []
        for scr in script_path:
            new_scripts.append(os.path.abspath(scr))
        self.scripts.append(new_scripts)

    def add_script(self,script_path):
        self.scripts.append([os.path.abspath(script_path)])
    
    def add_folder(self,folder_path):
        self.folders.append(os.path.abspath(folder_path))

    def init_scripts(self):
        script_groups = []
        for scr_grp in self.scripts:
            script = ""
            for scr in scr_grp:
                scr = os.path.basename(scr)
                if scr.endswith("ps1"):
                    script += 'echo Executing '+scr+'\nPowershell.exe -executionpolicy remotesigned -File "C:\\ini\\' + scr + '"\n'
                elif scr.endswith(".bat"):
                    script += 'echo Executing '+scr+'\ncall C:\\ini\\' + scr + "\n"
                elif scr.endswith(".py"):
                    script += 'echo Executing '+scr+'\nSET RUN_DOTPY=python.exe C:\\ini\\' + scr + '\nset SCRIPT=\nIF EXIST "python.exe" (\n\tSET SCRIPT=%RUN_DOTPY%\n)\n%SCRIPT%'
                script += 'shutdown /r /t 30\n'
            script_groups.append(bytearray(script, "utf8"))
        return script_groups

    def build_geniso(self, output_dir):
        ordered_scripts = self.init_scripts()
        # Added installation logs
        counter = 0
        for script_group in ordered_scripts:
            add_next_script = b""
            if counter < len(ordered_scripts) + 1:
                add_next_script = b'reg.exe ADD "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnce" /f /v NextScript /t REG_SZ /d "C:\\ini\\init_script_' + bytearray(str(counter), "utf8") + b'.bat"\n'
            init_script = "@echo on\n> C:\\ini\\install_{}.log (\n".format(counter) + add_next_script + script_group + "\n)\n"
            tmp_dir = tempfile.mkdtemp()
            with open(os.path.join(tmp_dir, 'init_script_{}.bat'.format(counter)), 'wb') as file_w:
                file_w.write(init_script)
            counter = counter + 1
        
        for scr_grp in self.scripts:
            for scr in scr_grp:
                with open(scr,'rb') as file_r:
                    with open(os.path.join(tmp_dir, os.path.basename(scr)), 'wb') as file_w:
                        file_w.write(file_r.read())
        for cfg in self.configs:
            with open(cfg,'rb') as file_r:
                with open(os.path.join(tmp_dir, os.path.basename(cfg)), 'wb') as file_w:
                    file_w.write(file_r.read())
        for folder in self.folders:
            copy_tree(folder, os.path.join(tmp_dir, os.path.basename(folder)))

        unmountCommand = 'genisoimage -o ' + output_dir + ' -J -R -l ' + str(tmp_dir)
        process = subprocess.Popen(unmountCommand.split(), stdout=subprocess.PIPE)
        out, err = process.communicate()
        p_status = process.wait()
        process.terminate()
        print(unmountCommand)
    
    def build_floppy(self, output_dir):
        if os.path.exists(output_dir):
            os.remove(output_dir)
        host_path = os.path.join(self.project_path, self.host.computer_name, 'iso_file')

        ordered_scripts = self.init_scripts()
        # Added installation logs
        counter = 0
        for script_group in ordered_scripts:
            add_next_script = b""
            if counter < len(ordered_scripts) + 1:
                add_next_script = b'reg.exe ADD "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnce" /f /v NextScript /t REG_SZ /d "C:\\ini\\init_script_' + bytearray(str(counter + 1), "utf8") + b'.bat"\n'
            init_script = b"@echo on\n> C:\\ini\\install_" + bytearray(str(counter), "utf8") + b".log (\n" + add_next_script + script_group + b"\n)\n"
            with open(os.path.join(host_path, 'init_script_{}.bat'.format(counter)), 'wb') as file_w:
                file_w.write(init_script.replace(b"\r",b"").replace(b"\n",b"\r\n"))
            counter = counter + 1
        
        for scr_grp in self.scripts:
            for scr in scr_grp:
                out_pth = os.path.join(host_path, os.path.basename(scr))
                if out_pth == scr:
                    continue
                with open(scr,'rb') as file_r:
                    with open(out_pth, 'wb') as file_w:
                        file_w.write(file_r.read().replace(b"\r",b"").replace(b"\n",b"\r\n"))
        for cfg in self.configs:
            out_pth = os.path.join(host_path, os.path.basename(cfg))
            if out_pth == cfg:
                continue
            with open(cfg,'rb') as file_r:
                with open(out_pth, 'wb') as file_w:
                    file_w.write(file_r.read().replace(b"\r",b"").replace(b"\n",b"\r\n"))
        for folder in self.folders:
            copy_tree(folder, os.path.join(host_path, os.path.basename(folder)))

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
        copy_tree(host_path, tmp_dir)

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

        iso.add_fp(BytesIO(init_script), len(init_script),'/INIT.;1',rr_name="init_script_0.bat",joliet_path='init_script_0.bat')

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
