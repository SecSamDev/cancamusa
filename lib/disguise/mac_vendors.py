import os
import random

MAC_LIST = []

def get_mac_list():
    if len(MAC_LIST) > 0:
        return MAC_LIST
    mac_list = []
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),'mac-vendor.txt'),'r') as mac_file:
        for line in mac_file.readlines():
            mac_list.append({'mac' : line[0:6].strip().lower(), 'vendor' : line[6:].strip()})
    return mac_list

MAC_LIST = get_mac_list()

def search_wildcard_vendor(mac_list, vendor="*"):
    vendor = vendor.lower()
    if vendor == '*':
        return mac_list[random.randint(0,len(mac_list))]
    elif(vendor.startswith("*") and vendor.endswith("*")):
        vendor = vendor[1:-1]
        for vendor_mac in mac_list:
            if(vendor in vendor_mac['mac']):
                return vendor_mac
    elif(vendor.startswith("*")):
        vendor = vendor[1:]
        for vendor_mac in mac_list:
            if(vendor_mac['mac'].endswith(vendor)):
                return vendor_mac
    elif(vendor.endswith("*")):
        vendor = vendor[:-1]
        for vendor_mac in mac_list:
            if(vendor_mac['mac'].startswith(vendor)):
                return vendor_mac
    else:
        for vendor_mac in mac_list:
            if(vendor in vendor_mac['mac']):
                return vendor_mac
    return mac_list[random.randint(0,len(mac_list))]

def random_mac_for_vendor(vendor):
    return ":".join([str(vendor[0:2]),str(vendor[2:4]),str(vendor[4:6]), rand_hex(),rand_hex(),rand_hex()])

def rand_hex():
    ret = hex(random.randint(0, 255)).lstrip("0x")
    if len(ret) == 1:
        ret = "0" + ret
    return ret