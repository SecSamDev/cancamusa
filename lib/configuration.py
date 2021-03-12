from __future__ import print_function, unicode_literals
from PyInquirer import prompt, print_json
import os
import json
from proxmox_utils import valid_proxmox_template_location, get_proxmox_storages, is_proxmox_system

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
                'win_images' : self.win_images
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
        except Exception as e:
            cancamusa = CancamusaConfiguration(pth)
        cancamusa.is_proxmox = is_proxmox_system()
        cancamusa.proxmox_storages = get_proxmox_storages()
        cancamusa.save()
        return cancamusa

    def select_win_image(self, host,debug=False):
        """Selects the best windows image for a given host

        Args:
            host (HostInfo): Windows HOST
        """
        
        for name, image in self.win_images.items():
            if image["windows"]["major"] == host.so.major:
                return image
        if debug:
            return {
                'windows' : {
                    'major' : 10,
                    'minor' : 0,
                },
                'versions' : ["Enterprise"],
                'path' : '/data/templates/iso/Windows10.iso'
            }
        raise Exception("Could not find a suitable image for the host {} with Windows {}".format(host.computer_name, host.so.major))



def configuration_mode():
    cancamusa_config = CancamusaConfiguration.load_or_create(None)
    while True:
        answers = prompt([{'type': 'list','name': 'option','message': 'Select an option', 'choices' : ['Set proxmox template location', 'Select proxmox ISO location', 'Select proxmox Extra ISO location', 'Edit registered Windows Images', 'Exit']}])
        storages = list(map(lambda x: x['name'], cancamusa_config.proxmox_storages))
        if answers['option'] == 'Set proxmox template location':
            answers = prompt([{'type': 'list','name': 'option','message': 'Select storage:', 'choices' : storages}])
            pos = storages.index(answers['option'])
            cancamusa_config.proxmox_templates = cancamusa_config.proxmox_storages[pos]['name']
        elif answers['option'] == 'Select proxmox ISO location':
            answers = prompt([{'type': 'list','name': 'option','message': 'Select storage:', 'choices' : storages}])
            pos = storages.index(answers['option'])
            cancamusa_config.proxmox_iso_storage = cancamusa_config.proxmox_storages[pos]['name']
        elif answers['option'] == 'Select proxmox Extra ISO location':
            answers = prompt([{'type': 'list','name': 'option','message': 'Select storage:', 'choices' : storages}])
            pos = storages.index(answers['option'])
            cancamusa_config.proxmox_iso_extra_storage = cancamusa_config.proxmox_storages[pos]['name']
        elif answers['option'] == 'Exit':
            cancamusa_config.save()
            exit()
        elif answers['option'] == 'Edit registered Windows Images':
            if len(cancamusa_config.win_images) == 0:
                print("No registered Windows Images")
            else:
                answers = prompt([{'type': 'list','name': 'selected_image','message': 'Registered images:', 'choices' : cancamusa_config.win_images.keys()},{'type' : 'list', 'name' : 'action', 'message' : 'What do you want to do?', 'choices' : ['Unregister image', 'Show']}])
                if answers['action'] == 'Unregister image':
                    cancamusa_config.win_images.pop(answers['selected_image'],None)
                elif answers['action'] == 'Show':
                    image = cancamusa_config.win_images[answers['selected_image']]
                    print(image)

