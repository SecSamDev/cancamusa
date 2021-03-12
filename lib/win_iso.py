import hashlib
from sys import platform
import json
import re
import os
import sys
from cancamusa_common import get_win_type
import subprocess

class WindowsImage:
    def __init__(self,iso,md5,win_type,images):
        self.iso = iso
        self.md5 = md5
        self.win_type = win_type
        self.images = images
    
    def __repr__(self):
        ret = "iso={}\nmd5={}\n".format(self.iso, self.md5)
        for image in self.images:
            ret += "{}:{}\n".format(image['id'], image['name'])
        return ret

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_windows_list(content):
    pattrn = 'Index\\s*:\\s*([0-9]+)\\s*Name\\s*:\\s*(.*)'
    pattern = re.compile(pattrn, re.MULTILINE)
    try:
        if platform == 'win32':
            matched = re.findall(pattern, str(content.decode('iso-8859-1')))
            to_ret = []
            for mtch in matched:
                to_ret.append({
                    'id' : mtch[0],
                    'name' : mtch[1]
                })
            return to_ret
        else:
            matched = re.findall(pattern, content.decode(sys.stdin.encoding))
            to_ret = []
            for mtch in matched:
                to_ret.append({
                    'id' : mtch[0],
                    'name' : mtch[1]
                })
            return to_ret
    except:
        matched = re.findall(pattern, str(content.decode("utf-8") ))
        to_ret = []
        for mtch in matched:
            to_ret.append({
                'id' : mtch[0],
                'name' : mtch[1]
            })
        return to_ret

def process_windows_image(win_image):
    print('Calculating MD5 of ISO image...')
    md5_value = md5(win_image)
    print('MD5 = ' + md5_value)

    print('Checking Windows Image Type...')
    # First mount image
    isoMountPath = '/mnt/' + md5_value
    if not os.path.isdir(isoMountPath):
        os.makedirs(isoMountPath)
    mountCommand = 'mount -o loop ' + win_image + ' ' + isoMountPath
    process = subprocess.Popen(mountCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    p_status = process.wait()
    process.terminate()
    # Process image wsim
    wimIMageCommand = 'wimlib-imagex info ' + isoMountPath +'/sources/install.wim'
    process = subprocess.Popen(wimIMageCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    p_status = process.wait()
    process.terminate()
    # Unmount image
    unmountCommand = 'umount ' + isoMountPath
    process = subprocess.Popen(unmountCommand.split(), stdout=subprocess.PIPE)
    out, err = process.communicate()
    p_status = process.wait()
    process.terminate()
    windows_list = get_windows_list(output)

    print('Available windows images:')
    for img in windows_list:
        print(str(img['id']) + " " + img['name'])
        win_type = get_win_type(img['name'])
    return {"iso" : win_image, "md5" : md5_value, "win_type" : win_type, "images" : windows_list}