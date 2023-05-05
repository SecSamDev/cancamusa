from lib.disguise.bios_database import BIOS_AMERICAN_MEGATREND_ALASKA_F5, BIOS_LIST
from PyInquirer import prompt

"""
 Creates a clone of a real machine to use in a virtualized network of the corporation.
 The generated machine is a stuntmachine (stuntman) of the real machine.
 This script needs info extracted using "extract-info.ps1"
"""
class HostInfoBios:
    def __init__(self, bios):
        self.manufacturer = bios['Manufacturer']
        self.version = bios['Version']
        self.caption = bios['Caption']
        self.description = bios['Description']
        self.release_date = bios['ReleaseDate']
        self.name = bios['Name']
        self.software_element_id = bios['SoftwareElementID']
        self.software_element_state = bios['SoftwareElementState']
        self.system_bios_major_version = bios['SystemBiosMajorVersion']
        self.system_bios_minor_version = bios['SystemBiosMinorVersion']
        self.smbios_major_version = bios['SMBIOSMajorVersion']
        self.smbios_minor_version = bios['SMBIOSMinorVersion']
        self.embedded_controller_major_version = bios['EmbeddedControllerMajorVersion']
        self.embedded_controller_minor_version = bios['EmbeddedControllerMinorVersion']
        self.ps_computer_name = bios['PSComputerName']
        self.smbios_bios_version = bios['SMBIOSBIOSVersion']

    def __str__(self):
        return "Manufacturer {}. Name: {}, Version: {}.".format(self.manufacturer, self.name, self.version)

    def edit_interactive(self):
        property_names = list(map(lambda x: str(x), dir(self)))
        class_props = list(map(lambda x: str(x), dir(HostInfoBios)))
        for element in class_props:
            property_names.pop(property_names.index(element))

        for prop in property_names:
            if prop.startswith("_"):
                continue
            answer = prompt([{'type': 'input', 'name': 'option', 'message': 'Edit: ' +
                              str(prop), 'default': str(getattr(self, prop))}])
            setattr(self, prop, answer['option'])
        return self

    def create_interactive():
        examples = ['Custom', 'Back'] + BIOS_LIST
        answer = prompt([{'type': 'list', 'name': 'option',
                          'message': 'Select a bios: ', 'choices': examples}])
        if answer['option'] == 'Custom':
            bios = HostInfoBios(
                BIOS_AMERICAN_MEGATREND_ALASKA_F5)
            bios.edit_interactive()
            return bios
        if answer['option'] == 'Back':
            return

    def to_json(self):
        return {
            'Manufacturer': self.manufacturer,
            'Version': self.version,
            'Caption': self.caption,
            'Description': self.description,
            'ReleaseDate': self.release_date,
            'Name': self.name,
            'SoftwareElementID': self.software_element_id,
            'SoftwareElementState': self.software_element_state,
            'SystemBiosMajorVersion': self.system_bios_major_version,
            'SystemBiosMinorVersion': self.system_bios_minor_version,
            'SMBIOSMajorVersion': self.system_bios_minor_version,
            'SMBIOSMinorVersion': self.system_bios_minor_version,
            'EmbeddedControllerMajorVersion': self.embedded_controller_major_version,
            'EmbeddedControllerMinorVersion': self.embedded_controller_minor_version,
            'PSComputerName': self.ps_computer_name,
            'SMBIOSBIOSVersion': self.smbios_bios_version,
        }

    def from_json(obj):
        return HostInfoBios(obj)