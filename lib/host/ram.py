from PyInquirer import prompt
from lib.host.common import size_numeric_to_textual, size_textual_to_numeric

class HostInfoRAM:
    def __init__(self, manufacturer,capacity):
        self.manufacturer = manufacturer
        self.capacity = int(capacity)

    def __str__(self):
        return "{} {}".format(self.manufacturer,size_numeric_to_textual(self.capacity))

    def edit_interactive(self):
        answer = prompt([{'type': 'input', 'name': 'option',
                          'message': 'Manufacturer', 'default': self.manufacturer}])
        self.manufacturer = answer['option']
        answer = prompt([{'type': 'input', 'name': 'option',
                          'message': 'Capacity:', 'default': str(size_numeric_to_textual(self.capacity))}])
        self.capacity = int(size_textual_to_numeric(answer['option']))
        
        return self

    def to_mib(self):
        return int(self.capacity / 1000000)

    def to_json(self):
        return {
            'Manufacturer': self.manufacturer,
            'Capacity': self.capacity,
        }

    def from_json(version_file):
        return HostInfoRAM(version_file['Manufacturer'], int(version_file['Capacity']))