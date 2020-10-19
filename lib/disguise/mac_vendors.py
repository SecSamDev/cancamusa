import os
import random

MAC_LIST = []

def get_mac_list():
    if len(MAC_LIST) > 0:
        return MAC_LIST
    mac_list = []
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),'mac-vendor.txt'),'r') as mac_file:
        for line in mac_file: 
            mac_list.append({'mac' : line[0:6].strip(), 'vendor' : line[6:].strip()})
    return mac_list

MAC_LIST = get_mac_list()

def search_wildcard_vendor(mac_list, vendor="*"):
    if vendor == '*':
        return mac_list[random.randint(0,len(mac_list))]
    elif(vendor.startswith("*") and vendor.endswith("*")):
        vendor = vendor[1:-1]
        for vendor_mac in mac_list:
            if(vendor in vendor_mac['vendor']):
                return vendor_mac
    elif(vendor.startswith("*")):
        vendor = vendor[1:]
        for vendor_mac in mac_list:
            if(vendor_mac['vendor'].endswith(vendor)):
                return vendor_mac
    elif(vendor.endswith("*")):
        vendor = vendor[:-1]
        for vendor_mac in mac_list:
            if(vendor_mac['vendor'].startswith(vendor)):
                return vendor_mac
    else:
        for vendor_mac in mac_list:
            if(vendor in vendor_mac['vendor']):
                return vendor_mac
    return mac_list[random.randint(0,len(mac_list))]
