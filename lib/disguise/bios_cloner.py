import os
import re
from random import randrange
from cancamusa_host import HostInfoBios
import tempfile
import subprocess
import os, shutil

def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)

def replace_files(file_list=[], replacer_list=[]):
    for file_name in file_list:
        data = ""
        with open(file_name, 'r') as file_data:
            data = file_data.read()
            for replacer in replacer_list:
                data = data.replace(replacer[0], replacer[1])
        with open(file_name, 'w') as file_data:
            file_data.write(data)

def process_release_date(released):
        #Format: 20120305000000.000000+000
        regex= r"^(?P<year>[0-9]{4})(?P<month>[0-9]{2})(?P<day>[0-9]{2})"
        matches= re.search(regex, released)
        return matches.group('day') + "/" + matches.group('month') + "/" + matches.group('year')

# git clone https://git.seabios.org/seabios.git
# or https://github.com/coreboot/seabios
# qemu -bios out/bios.bin
# https://gist.github.com/doomedraven/41af84c8cf93ba63cea933a80e898fb6

def download_seabios():
    SEABIOS_PATH = tempfile.mkdtemp()
    process = subprocess.Popen(['git','clone','https://github.com/coreboot/seabios.git'], stdout=subprocess.PIPE, cwd=SEABIOS_PATH)
    output, error = process.communicate()
    p_status = process.wait()
    process.terminate()
    SEABIOS_PATH = os.path.join(SEABIOS_PATH,'seabios')
    return SEABIOS_PATH

def compile_cloned_bios(bios,output_bios, SEABIOS_PATH=None):
    """[summary]
    Use information extracted from a Windows machine to compile a seabios that shows the same
    information as te original one.
    Information extracted using: Get-WmiObject Win32_Bios | ConvertTo-Json
    Args:
        bios (string): [description]

    Returns:
        [type]: [description]
    """
    if not SEABIOS_PATH:
        # TODO: escape character "
        # do git clone
        SEABIOS_PATH = tempfile.mkdtemp()
        process = subprocess.Popen(['git','clone','https://git.seabios.org/seabios.git'], stdout=subprocess.PIPE, cwd=SEABIOS_PATH)
        output, error = process.communicate()
        p_status = process.wait()
        process.terminate()
        SEABIOS_PATH = os.path.join(SEABIOS_PATH,'seabios')
    else:
        SEABIOS_PATH2 = tempfile.mkdtemp()
        copytree(SEABIOS_PATH,SEABIOS_PATH2)
        SEABIOS_PATH = SEABIOS_PATH2

    print("Working on: {}".format(SEABIOS_PATH) )
    SRC_CONFIG_H = os.path.join(SEABIOS_PATH, "src", "config.h")
    SRC_FW_SSDT_MISC_DSL = os.path.join(SEABIOS_PATH, "src", "fw", "ssdt-misc.dsl")
    VGASRC_KCONFIG = os.path.join(SEABIOS_PATH, "vgasrc", "Kconfig")
    SRC_HW_BLOCKCMD_C = os.path.join(SEABIOS_PATH, "src", "hw", "blockcmd.c")
    SRC_FW_ACPI_C = os.path.join(SEABIOS_PATH, "src", "fw", "acpi.c")
    SRC_FW_PARAVIRT_C = os.path.join(SEABIOS_PATH, "src", "fw", "paravirt.c")
    SRC_HW_BLOCKCMD_C = os.path.join(SEABIOS_PATH, "src", "hw", "blockcmd.c")
    SRC_STD_MPTABLE_H = os.path.join(SEABIOS_PATH, "src", "std", "mptable.h")
    SRC_FW_ACPI_DSDT_DSL = os.path.join(SEABIOS_PATH, "src", "fw", "acpi-dsdt.dsl")
    SRC_FW_Q35_ACPI_DSDT_DSL = os.path.join(
        SEABIOS_PATH, "src", "fw", "q35-acpi-dsdt.dsl")
    SRC_FW_SSDT_PCIHP_DSL = os.path.join(
        SEABIOS_PATH, "src", "fw", "ssdt-pcihp.dsl")
    SRC_FW_SSDT_PROC_DSL = os.path.join(SEABIOS_PATH, "src", "fw", "ssdt-proc.dsl")
    SRC_FW_PCIINIT_c = os.path.join(SEABIOS_PATH, "src", "fw", "pciinit.c")
    SRC_FW_BIOSTABLES_c = os.path.join(SEABIOS_PATH, "src", "fw", "biostables.c")
    SRC_FW_CSMC_C = os.path.join(SEABIOS_PATH, "src", "fw", "csm.c")
    SRC_OUTPUT_C = os.path.join(SEABIOS_PATH, "src", "output.c")

    NEW_BIOS_NAME_UPPER = bios.version.split(" ")[0]
    NEW_BIOS_NAME = NEW_BIOS_NAME_UPPER[0] + (NEW_BIOS_NAME_UPPER[1:]).lower()

    DOT_CONFIG = os.path.join(SEABIOS_PATH, ".config")
    MAKEFILE = os.path.join(SEABIOS_PATH, "Makefile")

    """data = ""
    with open(SRC_FW_PCIINIT_c, 'r') as file_data:
        data = file_data.read()
    data = re.sub(r'"Intel IGD BDSM enabled at[^"]+"', '"' + bios.name + '");', data)
    data = data.replace(", (u32)addr, bdsm_size >> 20, dev);","")
    with open(SRC_FW_PCIINIT_c, 'w') as file_data:
        file_data.write(data)
    """
    replace_files([SRC_FW_BIOSTABLES_c], [
        ['#define BIOS_NAME "SeaBIOS"', '#define BIOS_NAME "' + bios.manufacturer +'"'],
        ['#define BIOS_DATE "04/01/2014"', '#define BIOS_DATE "' + process_release_date(bios.release_date) +'"']
    ])
    BIOS_VENDOR = (NEW_BIOS_NAME_UPPER + "CPU00000000")[0:8]
    replace_files([SRC_CONFIG_H], [
        ["Bochs", NEW_BIOS_NAME],
        ["BOCHSCPU", BIOS_VENDOR],
        ["BOCHS ", NEW_BIOS_NAME_UPPER + " "],
        ["BXPC", NEW_BIOS_NAME_UPPER],
        ['"BXPC"', '"' + NEW_BIOS_NAME_UPPER + '"']
    ])
    replace_files([SRC_FW_ACPI_C], [
        [", BUILD_APPNAME6, 6", ', BUILD_APPNAME6, ' + str(len(NEW_BIOS_NAME_UPPER) + 1)],
        [", BUILD_APPNAME4, 4", ', BUILD_APPNAME4, ' + str(len(NEW_BIOS_NAME) + 1)],
        #BUILD_APPNAME8 in src/fw/mptable.c alredy has a size() method 
    ])
    
    HID_BIOS_NAME = re.sub('[^0-9a-fA-F]','0',NEW_BIOS_NAME_UPPER)
    HID_BIOS_NAME = (HID_BIOS_NAME + "00000000")[0:8]

    replace_files([SRC_FW_SSDT_MISC_DSL], [
        ["QEMU0001", HID_BIOS_NAME]
    ])
    """
    replace_files([SRC_STD_MPTABLE_H],[
        ["char oemid[8];", 'char oemid[{}];'.format(str(len(NEW_BIOS_NAME_UPPER)))]
    ])"""
    replace_files([VGASRC_KCONFIG], [
        ["QEMU/Bochs", NEW_BIOS_NAME],
        ["QEMU", NEW_BIOS_NAME],
        ["qemu bochs", NEW_BIOS_NAME],
        ["qemu", NEW_BIOS_NAME],
        ["bochs", NEW_BIOS_NAME]
    ])
    replace_files([SRC_HW_BLOCKCMD_C], [
        ['"QEMU", 5', '"' + BIOS_VENDOR[0:7] + '", 8']
    ])
    """
    replace_files([SRC_FW_PARAVIRT_C], [
        # Used for cdbres_inquiry.vendor -> char[8]
        ['"QEMU', '"' + BIOS_VENDOR],
        ["for (i = 0; i < 4; i++)","for (i = 0; i < {}; i++)".format(str(len(NEW_BIOS_NAME_UPPER)))]
    ])
    """

    replace_files([SRC_FW_ACPI_DSDT_DSL, SRC_FW_Q35_ACPI_DSDT_DSL], [
        ['"BXPC"', '"' + NEW_BIOS_NAME_UPPER + '"'],
        ['"BXDSDT"', '"' + NEW_BIOS_NAME_UPPER + '"']
    ])

    replace_files([SRC_FW_SSDT_PCIHP_DSL], [
        ['"BXPC"', '"' + NEW_BIOS_NAME_UPPER + '"'],
        ['"BXDSDT"', '"' + NEW_BIOS_NAME_UPPER + '"'],
        ['"BXSSDTPCIHP"', '"' + NEW_BIOS_NAME_UPPER + '"']
    ])

    replace_files([SRC_FW_SSDT_PROC_DSL], [
        ['"BXPC"', '"' + NEW_BIOS_NAME_UPPER + '"'],
        ['"BXDSDT"', '"' + NEW_BIOS_NAME_UPPER + '"']
    ])

    replace_files([SRC_FW_SSDT_MISC_DSL], [
        ['"BXPC"', '"' + NEW_BIOS_NAME_UPPER + '"'],
        ['"BXSSDTSU"', '"' + NEW_BIOS_NAME_UPPER + '"'],
        ['"BXSSDTSUSP"', '"' + NEW_BIOS_NAME_UPPER + '"']
    ])
    replace_files([SRC_FW_Q35_ACPI_DSDT_DSL, SRC_FW_ACPI_DSDT_DSL, SRC_FW_SSDT_MISC_DSL, SRC_FW_SSDT_PROC_DSL, SRC_FW_SSDT_PCIHP_DSL], [
        ['"BXPC"', '"' + NEW_BIOS_NAME_UPPER + '"']
    ])

    replace_files([SRC_FW_CSMC_C], [
        ['.OemIdStringPointer = (u32)"SeaBIOS",', '.OemIdStringPointer = (u32)"' + bios.manufacturer + '",']
    ])
    replace_files([SRC_OUTPUT_C], [
        ['"SeaBIOS (version', '" ' + bios.manufacturer + ' (version']
    ])

    # Create .config file
    process = subprocess.Popen(['make'], stdout=subprocess.PIPE, cwd=SEABIOS_PATH)
    output, error = process.communicate()
    p_status = process.wait()
    process.terminate()

    # Replace .config strings
    replace_files([DOT_CONFIG], [
        ['CONFIG_XEN=y', 'CONFIG_XEN=n']
    ])
    replace_files([MAKEFILE], [
        ['PYTHON=python','PYTHON=python3']
    ])
    # Compile
    process = subprocess.Popen(['make'], stdout=subprocess.PIPE, cwd=SEABIOS_PATH)
    output, error = process.communicate()
    p_status = process.wait()
    process.terminate()

    print("Generated SeaBIOS: {}".format(os.path.join(SEABIOS_PATH,"out","bios.bin")))
    # Move bios to new location
    with open(output_bios,'wb') as write_file:
        with open(os.path.join(SEABIOS_PATH,"out","bios.bin"),'rb') as read_file:
            write_file.write(read_file.read())
