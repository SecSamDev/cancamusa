import re
import random

def size_textual_to_numeric(text):
    pattern = '^([0-9]+)([GMKB])$'
    pattern = re.compile(pattern)
    convert = re.findall(pattern, text)
    if not convert or len(convert) != 1:
        raise Exception("Invalid format, must be: [0-9]+[GMKB]")
    total_size = 0
    convert = convert[0]
    if convert[1] == 'G':
        total_size = int(convert[0]) * 1024 * 1024 * 1024
    elif convert[1] == 'M':
        total_size = int(convert[0]) * 1024 * 1024
    elif convert[1] == 'K':
        total_size = int(convert[0]) * 1024
    elif convert[1] == 'B':
        total_size = int(convert[0])
    return total_size


def random_free_size(total_size):
    return random.randint(20*total_size, 60*total_size)


def next_letter(letter):
    print(letter)
    return chr(ord(letter) + 1)


def size_numeric_to_textual(total_size):
    if total_size > 1000000000:
        size = int(total_size/1000000000)
        if (total_size % 1000000000) < 100000000:
            return str(size) + "G"
    elif total_size > 1000000:
        size = int(total_size/1000000)
        if (total_size % 1000000) < 1000:
            return str(size) + "M"
    elif total_size > 1000:
        size = int(total_size/1000)
        return str(size) + "K"

    return str(total_size)+"B"


def filter_service_account(accounts):
    ret_acc = []
    for acc in accounts:
        if acc.name in ['WDAGUtilityAccount', 'DefaultAccount', 'Invitado', 'Guest']:
            continue
        if acc.name.startswith("SM_"):
            continue
        if acc.name.startswith("$_"):
            continue
        if acc.name.startswith("HealthMailbox"):
            continue
        ret_acc.append(acc)
    return ret_acc


def filter_kernel_interfaces(interfaces):
    ret_acc = []
    for acc in interfaces:
        if acc.description in ['WAN Miniport']:
            continue
        ret_acc.append(acc)
    return ret_acc
