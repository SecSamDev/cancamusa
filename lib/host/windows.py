from PyInquirer import prompt

from lib.cancamusa_common import get_win_type

class HostInfoWindowsVersion:
    def __init__(self, name, major, minor, build, revision, major_revision, minor_revision):
        self.name = name
        self.major = major
        self.minor = minor
        self.build = build
        self.revision = revision
        self.major_revision = major_revision
        self.minor_revision = minor_revision
        self.win_type = get_win_type(self.name)

    def __str__(self):
        return "{} ({})".format(self.name, self.build)

    def edit_interactive(self):
        answer = prompt([{'type': 'list', 'name': 'option',
            'message': 'Select a Windows type:', 'choices': ['Basic Edit','Full Edit']}])
        if answer['option'] == 'Basic Edit':
            answer = prompt([{'type': 'list', 'name': 'option',
            'message': 'Select a Windows type:', 'choices': ['Win7','Win8.1','Win10','Win11','Win2008r2','Win2012r2','Win2016','Win2019']}])
            if answer['option'] == 'Win10':
                self.name = 'Windows 10'
                self.major = 10
                self.minor = 0
                self.build = 1909
                self.revision = 18363
                self.major_revision = 1
                self.minor_revision = 0
            elif answer['option'] == 'Win11':
                self.name = 'Windows 11'
                self.major = 10
                self.minor = 0
                self.build = 1909
                self.revision = 18363
                self.major_revision = 1
                self.minor_revision = 0
            elif answer['option'] == 'Win7':
                self.name = 'Windows 7'
                self.major = 6
                self.minor = 1
                self.build = 7601
                self.revision = 65536
                self.major_revision = 1
                self.minor_revision = 0
            elif answer['option'] == 'Win8.1':
                self.name = 'Windows 8.1'
                self.major = 6
                self.minor = 1
                self.build = 7601
                self.revision = 65536
                self.major_revision = 1
                self.minor_revision = 0
            elif answer['option'] == 'Win2008r2':
                self.name = 'Windows Server 2008 R2'
                self.major = 6
                self.minor = 1
                self.build = 7600
                self.revision = 1
                self.major_revision = 1
                self.minor_revision = 0
            elif answer['option'] == 'Win2012r2':
                self.name = 'Windows Server 2012 R2'
                self.major = 6
                self.minor = 2
                self.build = 7600
                self.revision = 1
                self.major_revision = 1
                self.minor_revision = 0
            elif answer['option'] == 'Win2016':
                self.name = 'Windows Server 2016'
                self.major = 10
                self.minor = 0
                self.build = 14393
                self.revision = 1607
                self.major_revision = 1
                self.minor_revision = 0
            elif answer['option'] == 'Win2019':
                self.name = 'Windows Server 2019'
                self.major = 10
                self.minor = 0
                self.build = 19041
                self.revision = 1
                self.major_revision = 1
                self.minor_revision = 0
            
            self.win_type = answer['option']
        else:
            answer = prompt([{'type': 'input', 'name': 'option',
                'message': 'Select OS name', 'default': self.name}])
            self.name = answer['option']
            answer = prompt([{'type': 'input', 'name': 'option',
                'message': 'Select OS Major Version', 'default': str(self.major)}])
            self.major = int(answer['option'])
            answer = prompt([{'type': 'input', 'name': 'option',
                'message': 'Select OS Minor Version', 'default': str(self.minor)}])
            self.minor = int(answer['option'])
            answer = prompt([{'type': 'input', 'name': 'option',
                'message': 'Select OS Build Version', 'default': str(self.build)}])
            self.build = answer['option']
            answer = prompt([{'type': 'input', 'name': 'option',
                'message': 'Select OS revision Version', 'default': str(self.revision)}])
            self.revision = answer['option']
            answer = prompt([{'type': 'input', 'name': 'option',
                'message': 'Select OS major revision Version', 'default': str(self.major_revision)}])
            self.major_revision = int(answer['option'])
            answer = prompt([{'type': 'input', 'name': 'option',
                'message': 'Select OS minor revision Version', 'default': str(self.minor_revision)}])
            self.minor_revision = int(answer['option'])
        pass

    def to_json(self):
        return {
            'Name': self.name,
            'Major': self.major,
            'Minor': self.minor,
            'Build': self.build,
            'Revision': self.revision,
            'MajorRevision': self.major_revision,
            'MinorRevision': self.minor_revision
        }

    def from_json(version_file):
        if not 'Name' in version_file:
            version_file['Name'] = 'Windows 10 Enterprise'
        return HostInfoWindowsVersion(version_file['Name'], version_file['Major'], version_file['Minor'], version_file['Build'], version_file['Revision'], version_file['MajorRevision'], version_file['MinorRevision'])
