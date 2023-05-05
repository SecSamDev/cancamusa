from PyInquirer import prompt

from lib.host.common import next_letter, random_free_size, size_numeric_to_textual, size_textual_to_numeric

class HostInfoDisk:
    def __init__(self, device_id, volume_name, size, free_space):
        self.device_id = device_id[0]  # Only letter
        self.volume_name = volume_name
        self.size = size
        self.free_space = free_space

    def __str__(self):
        return "{}: {} ({})".format(self.device_id, self.volume_name, size_numeric_to_textual(self.size))

    def edit_interactive(self):
        answer = prompt([{'type': 'input', 'name': 'option',
                          'message': 'Select device ID', 'default': self.device_id}])
        if len(answer['option']) != 1:
            print("Drive letter must be 1 character long")
            return
        else:
            self.device_id = answer['option']
        answer = prompt([{'type': 'input', 'name': 'option',
                          'message': 'Volume name', 'default': self.volume_name}])
        self.volume_name = answer['option']
        answer = prompt([{'type': 'input', 'name': 'option', 'message': 'Disk Size.',
                          'default': size_numeric_to_textual(self.size)}])
        size = size_textual_to_numeric(answer['option'])
        self.size = size
        self.free_space = random_free_size(size)
        return self

    def create_interactive(last_leter="B", computer_name="My PC"):
        disk = HostInfoDisk(next_letter(last_leter), computer_name, 64098583552, 20828822016)
        disk = disk.edit_interactive()
        return disk

    def to_json(self):
        return {
            'DeviceID': self.device_id,
            'VolumeName': self.volume_name,
            'Size': self.size,
            'FreeSpace': self.free_space
        }

    def from_json(obj):
        return HostInfoDisk(obj['DeviceID'], obj['VolumeName'], obj['Size'], obj['FreeSpace'])
