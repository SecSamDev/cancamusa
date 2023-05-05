from PyInquirer import prompt
import re

class HostInfoCpu:
    def __init__(self, name, cores, threads):
        self.name = name
        self.family = "Intel"
        self.cores = cores
        self.threads = threads
        self.processor_type = "Haswell"
        self.architecture = "x64"

    def __str__(self):
        return "{} {} {}/{}".format(self.name,self.architecture, self.cores, self.threads)

    def edit_interactive(self):
        answer = prompt([{'type': 'input', 'name': 'option',
                          'message': 'Select CPU name', 'default': self.name}])
        self.name = answer['option']
        self.detect_cpu_family()
        answer = prompt([{'type': 'input', 'name': 'option',
                          'message': 'Cores:', 'default': str(self.cores)}])
        self.cores = int(answer['option'])
        answer = prompt([{'type': 'input', 'name': 'option',
                          'message': 'Threads: ', 'default': str(self.threads)}])
        self.threads = int(answer['option'])
        answer = prompt([{'type': 'list', 'name': 'option',
            'message': 'Select a processor architecture:', 'choices': ['x86','x64','ARM64']}])
        self.architecture = answer['option']
        #answer = prompt([{'type': 'list', 'name': 'option','message': 'Select a QEMU cpu type:', 'choices': list_processors(self.family)}])
        #self.processor_type = answer['option']
        return self
    
    def safe_name(self):
        return re.sub(r'[^a-zA-Z0-9]',"",self.name)

    def detect_cpu_family(self):
        if 'Intel' in self.name:
            self.family = "Intel"
        elif 'AMD' in self.name:
            self.family = "AMD"
        else:
            self.family = None

    def to_json(self):
        return {
            'Name': self.name,
            'NumberOfCores': self.cores,
            'NumberOfLogicalProcessors': self.threads,
            'Family': self.family,
            'CpuType': self.processor_type,
            "Architecture" : self.architecture
        }

    def from_json(version_file):
        host = HostInfoCpu(version_file['Name'], version_file['NumberOfCores'], version_file['NumberOfLogicalProcessors'])
        if "Architecture" in version_file:
            host.architecture = version_file["Architecture"]
        return host