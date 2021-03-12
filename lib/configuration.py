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
        self.proxmox_templates = ""
        self.packer_location = ""
        self.is_proxmox = False
        self.proxmox_storages = []
        self.win_images = {}
    
    def save(self):
        if not self.config_path:
            raise Exception("Invalid config file path")
        with open(self.config_path, 'w') as config_file:
            config_file.write(json.dumps({
                'proxmox_templates' : self.proxmox_templates,
                'packer_location' : self.packer_location
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
            cancamusa.proxmox_templates = cancamusa_config.proxmox_templates
            cancamusa.packer_location = cancamusa_config.packer_location
        except:
            cancamusa = CancamusaConfiguration(pth)
        cancamusa.is_proxmox = is_proxmox_system()
        cancamusa.proxmox_storages = get_proxmox_storages()
        cancamusa.save()
        return cancamusa



def configuration_mode():
    cancamusa_config = CancamusaConfiguration.load_or_create(None)
    while True:
        answers = prompt([{'type': 'list','name': 'option','message': 'Select an option', 'choices' : ['Set proxmox template location', 'Edit registered Windows Images', 'Exit']}])
        if answers['option'] == 'Set proxmox template location':
            if not is_proxmox_system():
                print("Not a valid proxmox server")
                continue
            answers =  prompt([{'type': 'input','name': 'template_location','message': 'Where is the new proxmox template location?'}])
            valid_path = valid_proxmox_template_location(answers["template_location"])
            if not valid_path:
                print("Invalid path selected: " + answers["template_location"])
            else:
                cancamusa_config.proxmox_templates = os.path.abspath(answers["template_location"])

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

