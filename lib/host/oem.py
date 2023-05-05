from PyInquirer import prompt

class HostInfoOEM:
    def __init__(self):
        self.logo = None
        self.manufacturer = None
        self.support_phone = None
        self.support_url = None
        self.support_app_url = None
        self.model = None
    
    def to_json(self):
        return {
            'logo' : self.logo,
            'manufacturer' : self.manufacturer,
            'support_phone' : self.support_phone,
            'support_url' : self.support_url,
            'support_app_url' : self.support_app_url,
            'model' : self.model
        }

    def from_json(obj):
        oem = HostInfoOEM()
        if 'logo' in obj:
            oem.logo = obj['logo']
        if 'manufacturer' in obj:
            oem.manufacturer = obj['manufacturer']
        if 'support_phone' in obj:
            oem.support_phone = obj['support_phone']
        if 'support_url' in obj:
            oem.support_url = obj['support_url']
        if 'support_app_url' in obj:
            oem.support_app_url = obj['support_app_url']
        if 'model' in obj:
            oem.model = obj['model']
        return oem


    def edit_interactive(self, project=None):
        property_names = ['logo','model','manufacturer','support_phone','support_app_url']
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