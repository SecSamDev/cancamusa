from PyInquirer import prompt

class HostInfoScripts:
    def __init__(self):
        self.scripts = []
    
    def to_json(self):
        return {
            'scripts' : self.scripts
        }

    def from_json(obj):
        scrpt = HostInfoScripts()
        if 'scripts' in obj:
            scrpt.scripts = obj['scripts']
        return scrpt


    def edit_interactive(self, project=None):
        property_names = ['scripts']
        for prop in property_names:
            if prop.startswith("_"):
                continue
            if prop == 'logo':
                logos = list(project.config['logos'])
                logos.append('None')
                answer = prompt([{'type': 'list', 'name': 'option', 'message': 'Select a logo: ', 'choices': logos}])
                answer = answer['option'].strip()
                if len(answer) == 0 or answer == 'None':
                    answer = None
                setattr(self, prop, answer)
                continue
            answer = prompt([{'type': 'input', 'name': 'option', 'message': 'Edit: ' + str(prop), 'default': str(getattr(self, prop))}])
            answer = answer['option'].strip()
            if len(answer) == 0 or answer == 'None':
                answer = None
            setattr(self, prop, answer)
        return self