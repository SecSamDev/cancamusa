from datetime import date
from PyInquirer import prompt

from lib.cancamusa_common import PASSWORD_GENERATOR_FIRSTNAME_YEAR, PASSWORD_GENERATOR_USERNAME_YEAR

class HostInfoWindowsAccounts:
    def __init__(self, account, password_generator=PASSWORD_GENERATOR_FIRSTNAME_YEAR):
        self.name = account['Name']
        self.local_account = account['LocalAccount']
        self.account_type = account['AccountType']
        self.ps_computer_name = account['PSComputerName']
        self.description = account['Description']
        self.sid = account['SID']
        self.lockout = account['Lockout']
        self.password_changeable = account['PasswordChangeable']
        self.password_expires = account['PasswordExpires']
        self.password_required = account['PasswordRequired']
        if 'Password' in account:
            self.password = account['Password']
        else:
            self.password = 'CancamusaRocks123!'
        if 'Domain' in account:
            self.domain = account['Domain']
        else:
            self.domain = self.ps_computer_name
        self.password_generator = password_generator

    def edit_interactive(self, password_generator=PASSWORD_GENERATOR_FIRSTNAME_YEAR):
        # If needed change in cancamusa.json
        """
        property_names = list(map(lambda x: str(x), dir(self)))
        class_props = list(map(lambda x: str(x), dir(HostInfoWindowsAccounts)))
        for element in class_props:
            property_names.pop(property_names.index(element))
        """
        property_names = ['name','description','domain','password']
        for prop in property_names:
            if prop.startswith("_"):
                continue
            if prop == 'password':
                if self.password_generator == PASSWORD_GENERATOR_FIRSTNAME_YEAR:
                    self.password = self.name + str(date.today().year)
                elif self.password_generator == PASSWORD_GENERATOR_USERNAME_YEAR:
                    self.password = self.name + str(date.today().year)
            answer = prompt([{'type': 'input', 'name': 'option', 'message': 'Edit: ' +
                              str(prop), 'default': str(getattr(self, prop))}])
            setattr(self, prop, answer['option'])
        return self

    def __str__(self):
        return "{} : {}".format(self.name, self.description)

    def create_interactive(host_name="", password_generator=PASSWORD_GENERATOR_FIRSTNAME_YEAR):
        disk = HostInfoWindowsAccounts({
            'Name': 'Administrator',
            'LocalAccount': True,
            'AccountType': 512,
            'PSComputerName': host_name,
            'Description': "Cuenta integrada para el acceso como invitado al equipo o dominio",
            'SID': 'S-1-5-21-2718119982-1426233563-2378531167-500',
            'Lockout': False,
            'PasswordChangeable': True,
            'PasswordExpires': False,
            'PasswordRequired': True,
            'Domain' : host_name,
            'Password' : 'password'
        })
        disk = disk.edit_interactive(password_generator=password_generator)
        return disk

    def to_json(self):
        return {
            'Name': self.name,
            'LocalAccount': self.local_account,
            'AccountType': self.account_type,
            'PSComputerName': self.ps_computer_name,
            'Description': self.description,
            'SID': self.sid,
            'Lockout': self.lockout,
            'PasswordChangeable': self.password_changeable,
            'PasswordExpires': self.password_expires,
            'PasswordRequired': self.password_required,
            'Domain' : self.domain,
            'Password' : self.password
        }

    def from_json(account):
        return HostInfoWindowsAccounts(account)