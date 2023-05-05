from __future__ import print_function, unicode_literals
from PyInquirer import prompt
import sys
import os
import argparse
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib', 'host'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib','disguise'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib','scripter'))

from lib.project import CancamusaProject
from lib.configuration import configuration_mode, CancamusaConfiguration
from lib.win_iso import process_windows_image

program_description = """
Design a full operational Windows Domain with Domain Controllers, a Exchange server and a list of Windows hosts that can be based on real ones by cloning the configuration.
"""
parser = argparse.ArgumentParser(description=program_description)
parser.add_argument('--config', dest='configuration', action='store_true', default=False,
                    help='Enter configuration mode to edit cancamusa preferences')
parser.add_argument('--register-iso', dest='register_iso', action='store',
                    help='Register a Windows Image to use as base image')

args = parser.parse_args()

if args.configuration :
    configuration_mode()
    exit()
if args.register_iso :
    cancamusa_config = CancamusaConfiguration.load_or_create(None)
    
    if not cancamusa_config.iso_in_proxmox_path(args.register_iso) and cancamusa_config.is_proxmox:
        print("Iso Image not in a valid Proxmox storage folder")
    win_image = process_windows_image(args.register_iso)
    cancamusa_config.add_win_image(win_image)
    cancamusa_config.save()
    exit()

cancamusa = None
try:
    cancamusa = CancamusaProject.load_from_current_path()
except Exception as e:
    print(e)
    # Ask user if want a new project
    answers = prompt([{'type': 'confirm','name': 'new_project','message': 'Error loading project. Want to create a new Cancamusa project?'}])
    if answers['new_project']:
        cancamusa = CancamusaProject.new_project_in_current_path()
    else:
        exit()

# Do things with the configuration
cancamusa.edit_project_interactive()


