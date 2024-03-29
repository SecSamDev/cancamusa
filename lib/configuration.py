from __future__ import print_function, unicode_literals
from PyInquirer import prompt, print_json
import os
import json
from proxmox_utils import valid_proxmox_template_location, get_proxmox_storages, is_proxmox_system
from cancamusa_common import get_win_type, get_win_image_type

def get_cancamusa_home():
    if 'CANCAMUSA_HOME' in os.environ:
        cancamusa_home = os.environ['CANCAMUSA_HOME']
    else:
        user_home = os.path.expanduser("~")
        cancamusa_home = os.path.join(user_home,".cancamusa")
    if not os.path.isdir(cancamusa_home):
        try:
            os.mkdir(cancamusa_home)
        except:
            pass
    
    return cancamusa_home


class CancamusaConfiguration:
    def __init__(self, config_path):
        self.config_path = config_path
        self.proxmox_templates = None
        self.proxmox_iso_storage = "local"
        self.packer_location = None
        self.bios_location = None
        self.is_proxmox = False
        self.proxmox_storages = []
        self.win_images = {}
        self.proxmox_image_storage = "local"
        self.proxmox_iso_extra_storage = "local"
        self.start_vmbr = 1
    
    def save(self):
        if not self.config_path:
            raise Exception("Invalid config file path")
        with open(self.config_path, 'w') as config_file:
            config_file.write(json.dumps({
                'proxmox_templates' : self.proxmox_templates,
                'packer_location' : self.packer_location,
                'bios_location' : self.bios_location,
                'proxmox_storages' : self.proxmox_storages,
                'proxmox_iso_storage' : self.proxmox_iso_storage,
                'proxmox_iso_extra_storage' : self.proxmox_iso_extra_storage,
                'proxmox_image_storage' : self.proxmox_image_storage,
                'win_images' : self.win_images,
                'start_vmbr' : self.start_vmbr
            },indent=4,))
        return self
    
    def add_win_image(self, win_image):
        self.win_images[win_image['md5']] = win_image

    def iso_in_proxmox_path(self, iso_image):
        for storage in self.proxmox_storages:
            if iso_image.startswith(storage['path']):
                return True
        return False

    #def __repr__(self):
    #    return "".format(self.win_images)

    def load_or_create(pth):
        if pth == None:
            pth = os.path.join(get_cancamusa_home(),"preferences.json")
        
        try:
            cancamusa = CancamusaConfiguration(pth)
            with open(pth,'r') as cancamusa_file:
                cancamusa_config = json.loads(cancamusa_file.read())
            cancamusa.config_path = pth
            cancamusa.proxmox_templates = cancamusa_config['proxmox_templates']
            cancamusa.packer_location = cancamusa_config['packer_location']
            cancamusa.bios_location = cancamusa_config['bios_location']
            cancamusa.proxmox_storages = cancamusa_config['proxmox_storages']
            cancamusa.proxmox_iso_storage = cancamusa_config['proxmox_iso_storage']
            cancamusa.proxmox_image_storage = cancamusa_config['proxmox_image_storage']
            cancamusa.proxmox_iso_extra_storage = cancamusa_config['proxmox_iso_extra_storage']
            cancamusa.win_images = cancamusa_config['win_images']
            if 'start_vmbr' in cancamusa_config:
                cancamusa.start_vmbr = cancamusa_config['start_vmbr']
        except Exception as e:
            cancamusa = CancamusaConfiguration(pth)
        cancamusa.is_proxmox = is_proxmox_system()
        cancamusa.proxmox_storages = get_proxmox_storages()
        cancamusa.save()
        return cancamusa

    def select_win_image(self, host,debug=False,prompter=True,clean=False):
        """Selects the best windows image for a given host

        Args:
            host (HostInfo): Windows HOST
        """
        win_type = host.os.win_type
        if not win_type:
            win_type = get_win_type(host.os.name)
        win_image = get_win_image_type(str(host.os.name))
        if debug:
            return {
                'win_type' : win_image,
                "architecture" : "x64",
                'md5' : '00000',
                'images' : {'0' : 'Windows X Professional'},
                'selected_img' : 0,
                'path' : '/data/templates/iso/WindowsX.iso'
            }

        if host.selected_img_md5 != None and clean == False:
            selected_image = None
            for name, image in self.win_images.items():
                if host.selected_img_md5 == image['md5']:
                    selected_image = image
                    return {
                        'path' : image['path'],
                        'win_type' : image['win_type'],
                        "architecture" : image['architecture'],
                        'md5' : image['md5'],
                        'selected_img' : host.selected_img_idx,
                        'images' : image['images']
                    }
        
        # Failed to get an image
        select_image = []
        images = []
        for name, image in self.win_images.items():
            if image["win_type"] == win_type:
                select_image.append(image)
                images.append(os.path.basename(image['path']))
        #images = list(map(lambda x: os.path.basename(x['path']), select_image))
        if prompter:
            answer = prompt([{'type': 'list', 'name': 'option','message': 'Select a Windows Image for {} ({}):'.format(host.os.name, host.cpus[0].architecture), 'choices': images}])
            pos = images.index(answer['option'])
            selected_image = select_image[pos]
            image_ids = list(selected_image['images'].values())
            answer = prompt([{'type': 'list', 'name': 'option','message': 'Select a Windows Image ID for {}:'.format(host.os.name), 'choices': image_ids}])
            pos = image_ids.index(answer['option'])
            return {
                'path' : selected_image['path'],
                'win_type' : selected_image['win_type'],
                "architecture" : selected_image['architecture'],
                'md5' : selected_image['md5'],
                'selected_img' : pos,
                'images' : selected_image['images']
            }
        else:
            if len(select_image) == 0:
                raise BaseException("Cannot find a viable image for {}".format(host.computer_name))
            image = select_image[0].copy()
            image['selected_img'] = 0
            return image



def configuration_mode():
    cancamusa_config = CancamusaConfiguration.load_or_create(None)
    while True:
        answers = prompt([{'type': 'list','name': 'option','message': 'Select an option', 'choices' : ['Set proxmox template location', 'Select proxmox ISO location', 'Select proxmox Extra ISO location','Select proxmox Image location', 'Edit registered Windows Images','Network bridges', 'Exit']}])
        storages = list(map(lambda x: x['name'], cancamusa_config.proxmox_storages))
        if answers['option'] == 'Set proxmox template location':
            storages = []
            for strg in cancamusa_config.proxmox_storages:
                if 'template' in strg['type']:
                    storages.append(x['name'])
            if len(storages) == 0:
                print("Using default template location: /etc/pve/qemu-server/")
                cancamusa_config.proxmox_templates = '/etc/pve/qemu-server/'
                continue
            answers = prompt([{'type': 'list','name': 'option','message': 'Select storage:', 'choices' : storages}])
            pos = storages.index(answers['option'])
            cancamusa_config.proxmox_templates = cancamusa_config.proxmox_storages[pos]['path']
        elif answers['option'] == 'Select proxmox ISO location':
            answers = prompt([{'type': 'list','name': 'option','message': 'Select storage:', 'choices' : storages}])
            pos = storages.index(answers['option'])
            cancamusa_config.proxmox_iso_storage = cancamusa_config.proxmox_storages[pos]['name']
        elif answers['option'] == 'Select proxmox Extra ISO location':
            answers = prompt([{'type': 'list','name': 'option','message': 'Select storage:', 'choices' : storages}])
            pos = storages.index(answers['option'])
            cancamusa_config.proxmox_iso_extra_storage = cancamusa_config.proxmox_storages[pos]['name']
        elif answers['option'] == 'Select proxmox Image location':
            answers = prompt([{'type': 'list','name': 'option','message': 'Select storage:', 'choices' : storages}])
            pos = storages.index(answers['option'])
            cancamusa_config.proxmox_image_storage = cancamusa_config.proxmox_storages[pos]['name']
        elif answers['option'] == 'Network bridges':
            answers = prompt([{'type': 'input','name': 'option','message': 'Select Bridge index to create new ones:', 'default' : "1"}])
            try:
                val = int(answers['option'])
                if val > 0:
                    cancamusa_config.start_vmbr = val
                else:
                    cancamusa_config.start_vmbr = 1
            except:
                cancamusa_config.start_vmbr = 1
        elif answers['option'] == 'Exit':
            cancamusa_config.save()
            exit()
        elif answers['option'] == 'Edit registered Windows Images':
            if len(cancamusa_config.win_images) == 0:
                print("No registered Windows Images")
            else:
                answers = prompt([{'type': 'list','name': 'selected_image','message': 'Registered images:', 'choices' : cancamusa_config.win_images.keys()},{'type' : 'list', 'name' : 'action', 'message' : 'What do you want to do?', 'choices' : ['Unregister image', 'Show', 'Edit Architecture']}])
                if answers['action'] == 'Unregister image':
                    cancamusa_config.win_images.pop(answers['selected_image'],None)
                elif answers['action'] == 'Show':
                    image = cancamusa_config.win_images[answers['selected_image']]
                    print(image)
                elif answers['action'] == 'Edit Architecture':
                    answer = prompt([{'type': 'list', 'name': 'option',
                        'message': 'Select a processor architecture:', 'choices': ['x86','x64','ARM64']}])
                    cancamusa_config.win_images[answers['selected_image']]["architecture"] = answer["option"]

