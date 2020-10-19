import os
from sys import platform

def is_proxmox_system():
    return os.path.isdir('/etc/pve')

def regex_match(pattern,content):
    try:
        if platform == 'win32':
            return re.findall(pattern, str(content.decode('iso-8859-1')))
        else:
            return re.findall(pattern, content.decode(sys.stdin.encoding))
    except:
        return re.findall(pattern, str(content))

def get_proxmox_storages():
    try:
        with open('/etc/pve/storage.cfg','r') as storage_cfg:
            info = storage_cfg.readlines()
            storages = []
            storage_type = None
            storage_name = None
            storage_path = None
            dir_pattern = '^([^:]+)\s*:\s*(.*?)\$'
            dir_pattern = re.compile(dir_pattern)
            for line in info:
                matched = regex_match(dir_pattern, line)
                if line.trim() == "":
                    if storage_type:
                        storages.append({
                            'path' : storage_path,
                            'name' : storage_name,
                            'type' : storage_type
                        })
                    storage_name = None
                    storage_type = None
                    storage_path = None
                if matched:
                    storage_name = matched[1]
                else:
                    if 'path ' in line:
                        storage_path = line.split('path ')[1]
                    elif 'content ' in line:
                        storage_type = line.split('content ')[1].split(',')
            if storage_type:
                storages.append({
                    'path' : storage_path,
                    'name' : storage_name,
                    'type' : storage_type
                })
            return storages
    except:
        return []
                




def valid_proxmox_template_location(pth):
    if not os.path.isdir(pth):
        return False
    if os.path.abspath(pth) == os.path.abspath("/etc/pve/qemu-server"):
        return True
    # Unknown location, check if the files matches the name [0-9]+.conf
    file_list = os.listdir(pth)
    valid_path = False
    for host_conf in file_list:
        try:
            splited = host_conf.split(".")
            if len(splited) == 2 and int(splited[0]) > 0 and splited[1] == "conf":
                invalid_path = True
        except:
            pass
    
    return valid_path

def last_vm_id(pth):
    if not os.path.isdir(pth):
        raise Exception('Not a valid path')
    # Unknown location, check if the files matches the name [0-9]+.conf
    file_list = os.listdir(pth)
    last_id = -1
    for host_conf in file_list:
        try:
            splited = host_conf.split(".")
            if len(splited) == 2 and int(splited[0]) > 0 and splited[1] == "conf":
                if int(splited[0]) > last_id:
                    last_id = int(splited[0])
        except:
            pass
    
    return last_id