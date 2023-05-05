
class HostInfoRoles:
    def __init__(self, roles, config={}):
        self.roles = set()
        for rol in roles:
            self.roles.add(rol)
        self.config = config

    def edit_interactive(self):
        answer = prompt([{'type': 'checkbox', 'name': 'option',
                          'message': 'Select server roles: ', 'choices': [{'name': x, 'checked': (x in self.roles)} for x in AVAILABLE_ROLES]}])
        answ = answer['option']

        for rol in AVAILABLE_ROLES:
            if rol in answ:
                self.roles.add(rol)
            else:
                self.roles.remove(rol)
        for rol in self.roles:
            # Customize properties for each ROL
            # DNS: DNS user and password for DHCP Server
            # Don't save state as to prevent errors
            self.config[rol] = {}
            if rol == ROLE_DOMAIN_CONTROLLER:
                answer = prompt([{'type': 'input', 'name': 'option',
                          'message': 'Safe mode password: ', 'default' : 'SafeModePassw123!'}])
                self.config[rol]['safe_mode_password'] = answer['option']
            if rol == ROLE_DNS:
                answer = prompt([{'type': 'input', 'name': 'option',
                          'message': 'Select username for DhcpServer in DNS: ', 'default' : 'dnsadmin'}])
                self.config[rol]['username'] = answer['option']
                answer = prompt([{'type': 'input', 'name': 'option',
                          'message': 'Select password for DhcpServer in DNS: ', 'default' : 'password'}])
                self.config[rol]['password'] = answer['option']
                answer = prompt([{'type': 'input', 'name': 'option',
                          'message': 'External DNS server: ', 'default' : '8.8.8.8'}])
                self.config[rol]['forwarder'] = answer['option']
            if rol == ROLE_DHCP:
                answer = prompt([{'type': 'list', 'name': 'option',
                          'message': 'Failover mode: ', 'choices' : ['StandBy','Active']}])
                self.config[rol]['failover_mode'] = answer['option']
                if self.config[rol]['failover_mode'] == 'Active':
                    answer = prompt([{'type': 'input', 'name': 'option',
                            'message': 'Failover secret: ', 'default' : 'S3cret'}])
                    self.config[rol]['failover_secret'] = answer['option']
            if rol == ROLE_WEB_SERVER:
                # TODO
                self.config[rol] = {}
            if rol == ROLE_KMS:
                if not 'license_keys' in self.config[rol]:
                    self.config[rol]['license_keys'] = {}
                while True:
                    answer = prompt([{'type': 'list', 'name': 'option','message': 'Failover mode: ', 'choices' : ['Add','Remove','List','Exit']}])
                    # https://docs.microsoft.com/en-us/deployoffice/vlactivation/configure-a-kms-host-computer-for-office
                    if answer['option'] == 'Add':
                        answer = prompt([{'type': 'input', 'name': 'option', 'message': 'Windows Activation ID: ', 'default' : ''}])
                        answer2 = prompt([{'type': 'input', 'name': 'option', 'message': 'Windows Confirmation ID: ', 'default' : ''}])
                        self.config[rol]['license_keys'][answer['option']] = answer2['option']
                    elif answer['option'] == 'Remove':
                        answer = prompt([{'type': 'list', 'name': 'option','message': 'ActivationID: ', 'choices' : list(self.config[rol]['license_keys'].keys()) }])
                        self.config[rol]['license_keys'].pop(answer['option'],None)
                    elif answer['option'] == 'List':
                        print("{}".format(", ".join(list(self.config[rol]['license_keys'].keys()))))
                    elif answer['option'] == 'Exit':
                        break
            
        return self

    def create_interactive():
        roles = set()
        answer = prompt([{'type': 'checkbox', 'name': 'option',
                          'message': 'Select server roles: ', 'choices': [{'name': x, 'checked': (x in self.roles)} for x in AVAILABLE_ROLES]}])
        answ = answer['option']
        if len(answ) == 0:
            return HostInfoRoles([])
        else:
            for ans in answ:
                roles.add(ans)
            return HostInfoRoles(roles)

    def to_json(self):
        toRet = []
        for rol in self.roles:
            config = self.config[rol] if rol in self.config else {}
            toRet.append({
                'Name': rol,
                'Config' : config
            })
        return toRet

    def from_json(roles):
        if len(roles) > 0 and 'Name' in roles[0] and not 'DisplayName' in roles[0]:
            rols = []
            configs = {}
            for rol in roles:
                config = rol['Config'] if 'Config' in rol else {}
                configs[rol['Name']] = config
                rols.append(rol['Name'])
            return HostInfoRoles(rols, configs)
        elif len(roles) > 0 and 'Name' in roles[0] and 'DisplayName' in roles[0]:
            # Not processed
            role_list = roles_from_extracted_info(roles)
            return HostInfoRoles(role_list)
        else:
            return HostInfoRoles([])
