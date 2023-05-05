import os
import re
import subprocess
from lib.disguise.processors import get_processor

def is_proxmox_system():
    return os.path.isdir('/etc/pve')


def get_host_processor():
    all_info = subprocess.check_output("cat /sys/devices/cpu/caps/pmu_name", shell=True).strip()
    if all_info == "" and not 'CANCAMUSA_DEBUG' in os.environ:
        raise Exception("Cannot read processor type")
    return get_processor(all_info)

def get_proxmox_storages():
    try:
        with open('/etc/pve/storage.cfg','r') as storage_cfg:
            info = storage_cfg.readlines()
            storages = []
            storage_type = None
            storage_name = None
            storage_path = None
            dir_pattern = '^dir\\s*:\\s*(.*)'
            dir_pattern = re.compile(dir_pattern)
            for line in info:
                matched = re.match(dir_pattern, line)
                if line.strip() == "":
                    if storage_type:
                        storages.append({
                            'path' : storage_path,
                            'name' : storage_name,
                            'type' : storage_type
                        })
                        storage_name = None
                        storage_type = None
                        storage_path = None
                    continue
                if matched:
                    storage_name = matched[1]
                else:
                    if 'path ' in line:
                        storage_path = line.split('path ')[1].strip()
                    elif 'content ' in line:
                        storage_type = list(map(lambda x: x.strip(), line.split('content ')[1].split(',')))
            if storage_type:
                storages.append({
                    'path' : storage_path,
                    'name' : storage_name,
                    'type' : storage_type
                })
            return storages
    except Exception as e:
        print(e)
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