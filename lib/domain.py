from PyInquirer import prompt
from datetime import date
import cancamusa_common

class CancamusaDomain:
    def __init__(self, domains=[], default_admin_password='CancamusaRocks123!',password_generator=cancamusa_common.PASSWORD_GENERATOR_FIRSTNAME_YEAR):
        self.domains = domains
        self.default_admin_password = default_admin_password
        self.password_generator = password_generator
    
    def load_from_object(obj, default_admin_password='CancamusaRocks123!',password_generator=cancamusa_common.PASSWORD_GENERATOR_FIRSTNAME_YEAR):
        domains = []
        for dmn in obj["domains"]:
            domain = ADStructure.from_json(dmn)
            domain.default_admin_password = default_admin_password
            domain.password_generator = password_generator
            domains.append(domain)
        cancamusa = CancamusaDomain(domains,default_admin_password=default_admin_password,password_generator=password_generator)
        return cancamusa

    def get_domain(self,domain):
        for dmn in self.domains:
            if domain == dmn.domain:
                return dmn
        return None
    
    def get_domain_by_name(self,name):
        for dmn in self.domains:
            if name == dmn.name:
                return dmn
        return None

    def add_domain(self,domain):
        self.domains.append(domain)

    def exists_domain(self, short_name):
        for dmn in self.domains:
            if short_name == dmn.name:
                return True
        return False

    def edit_interactive(self):
        print("Domains:")
        for domain in self.domains:
            print(domain)
        while True:
            try:
                options =  ['Add domain','Import domains']
                if len(self.domains) > 0:
                    options.append('Show domains')
                    options.append('Edit domain')
                    options.append('Delete domain')
                options.append('Back')
                answer = prompt([{'type': 'list','name': 'option','message': 'Domain edition mode', 'choices' : options}])
                if answer['option'] == 'Show domains':
                    for domain in self.domains:
                        print(domain)
                elif answer['option'] == 'Add domain':
                    answer = prompt([{'type': 'input','name': 'option','message': 'Domain name:', 'default' : "cancamusa.com"}])
                    domain = ADStructure(answer['option'], default_admin_password=self.default_admin_password, password_generator=self.password_generator)
                    domain = domain.edit_interactive()
                    if domain:
                        self.add_domain(domain)
                elif answer['option'] == 'Edit domain':
                    domains = list(map(lambda x: x.domain, self.domains))
                    answer = prompt([{'type': 'list','name': 'option','message': 'Select a domain to edit', 'choices' :domains}])
                    pos = domains.index(answer['option'])
                    self.domains[pos].edit_interactive()
                elif answer['option'] == 'Delete domain':
                    domains = list(map(lambda x: x.domain, self.domains))
                    answer = prompt([{'type': 'list','name': 'option','message': 'Select a domain to delete', 'choices' :domains}])
                    pos = domains.index(answer['option'])
                    self.domains.pop(pos)
                elif answer['option'] == 'Back':
                    return
            except:
                pass

    def to_json(self):
        toret = {
            'domains' : []
        }
        for dm in self.domains:
            toret['domains'].append(dm.to_json())
        return toret

class ADStructure:
    def __init__(self, domain, default_admin_password='CancamusaRocks123!', password_generator=cancamusa_common.PASSWORD_GENERATOR_FIRSTNAME_YEAR):
        self.ou = {}
        self.domain = domain
        self.name = "CNCMS"
        dc_path_string = "DC=" + (",DC=".join(domain.split(".")))
        self.path = dc_path_string
        self.default_admin = 'Admin'
        self.account_generator = cancamusa_common.ACCOUNT_FORMAT_NAME_DOT_SURNAME
        self.default_admin_password = default_admin_password
        self.dc_ip = '10.0.0.1'
        self.kms_server = None
        self.password_generator = password_generator

    def get_user(self, username):
        users = self.list_users()
        for usr in users:
            if usr['account_name'] == username:
                return usr
        return None
    
    def from_json(obj):
        ret = ADStructure(obj["domain"], default_admin_password='CancamusaRocks123!', password_generator=cancamusa_common.PASSWORD_GENERATOR_FIRSTNAME_YEAR)
        for name, ou in obj["ou"].items():
            parsed_ou = ADOrganizationalUnit.from_json(ou,parent=ret)
            ret.ou[parsed_ou.name] = parsed_ou
        if 'name' in obj:
            ret.name = obj['name']
        if 'default_admin' in obj:
            ret.default_admin = obj['default_admin']
        if 'account_generator' in obj:
            ret.account_generator = obj['account_generator']
        if 'default_admin_password' in obj:
            ret.default_admin_password = obj['default_admin_password']
        if 'dc_ip' in obj:
            ret.dc_ip = obj['dc_ip']
        if 'kms_server' in obj:
            ret.kms_server = obj['kms_server']
        if 'default_admin_password' in obj:
            ret.default_admin_password = obj['default_admin_password']
        return ret

    def __str__(self):
        return "{} : {}".format(self.domain, self.path)

    def to_json(self):
        ret = {
            'ou' : {},
            'domain' : self.domain,
            'name' : self.name,
            'default_admin' : self.default_admin,
            'default_admin_password' : self.default_admin_password,
            'dc_ip' : self.dc_ip,
            'kms_server' : self.kms_server,
        }
        for name, ou in self.ou.items():
            ret['ou'][name] = ou.to_json(full=True)
        return ret

    def list_child_ou(self):
        ret = []
        for name, ou in self.ou.items():
            ret = ret + ou.list_child_ou()
        return ret
    
    def list_groups(self):
        ret = []
        for name, ou in self.ou.items():
            ret = ret + ou.list_groups()
        return ret
    
    def list_users(self):
        ret = []
        for name, ou in self.ou.items():
            ret = ret + ou.list_users()
        return ret

    def edit_interactive(self):
        while True:
            try:
                options =  ['Domain Name','Add OU','Import OUs']
                if len(self.ou) > 0:
                    options.append('Show OUs')
                    options.append('Show OU Tree')
                    options.append('Edit OU')
                    options.append('Delete OU')
                options.append('Account Generator')
                options.append('Default Local Admin')
                options.append('Default Local Admin Password')
                options.append('Set DC IP')
                options.append('Set KMS Server')
                options.append('Back')
                options.append('Cancel')
                answer = prompt([{'type': 'list','name': 'option','message': 'OrganizationalUnit edition mode:', 'choices' : options}])
                if answer['option'] == 'Show OUs':
                    for ou_name in self.ou.keys():
                        print(ou_name)
                if answer['option'] == 'Show OU Tree':
                    print(">" + self.name)
                    for ou_name, ou in self.ou.items():
                        print(ou.tree_str(1))
                elif answer['option'] == 'Add OU':
                    answer = prompt([{'type': 'input','name': 'option','message': 'OU name:', 'default' : ""}])
                    ou = ADOrganizationalUnit(answer['option'],self)
                    ou.account_generator = self.account_generator
                    ou = ou.edit_interactive()
                    if ou:
                        self.ou[ou.name] = ou
                elif answer['option'] == 'Domain Name':
                    answer = prompt([{'type': 'input','name': 'option','message': 'Domain Name:', 'default' : self.name}])
                    self.name = answer["option"]
                elif answer['option'] == 'Edit OU':
                    answer = prompt([{'type': 'list','name': 'option','message': 'Select a OU to edit:', 'choices' :self.ou.keys()}])
                    self.ou[answer['option']].account_generator = self.account_generator
                    self.ou[answer['option']].edit_interactive()
                elif answer['option'] == 'Account Generator':
                    answers = prompt([{'type': 'list','name': 'selection','message': 'Method used to generate random accounts. Ex: ' + cancamusa_common.ACCOUNT_FORMAT_EXAMPLE, 'choices' : [cancamusa_common.ACCOUNT_FORMAT_LETTER_SURNAME, cancamusa_common.ACCOUNT_FORMAT_NAME_DOT_SURNAME, cancamusa_common.ACCOUNT_FORMAT_TRHEE_LETTERS]}])
                    self.account_generator = answers['selection']
                elif answer['option'] == 'Default Local Admin':
                    answer = prompt([{'type': 'input','name': 'option','message': 'Admin name:', 'default' : self.default_admin}])
                    self.default_admin = answer["option"]
                elif answer['option'] == 'Default Local Admin Password':
                    answer = prompt([{'type': 'input','name': 'option','message': 'Admin password:', 'default' : self.default_admin_password}])
                    self.default_admin_password = answer["option"]
                elif answer['option'] == 'Delete OU':
                    answer = prompt([{'type': 'list','name': 'option','message': 'Select a OU to delete:', 'choices' :self.ou.keys()}])
                    self.ou.pop(answer["option"], None)
                elif answer['option'] == 'Back':
                    return self
                elif answer['option'] == 'Set DC IP':
                    answer = prompt([{'type': 'input','name': 'option','message': 'Principal DC IP:', 'default' : self.dc_ip}])
                    self.dc_ip = answer["option"]
                elif answer['option'] == 'Set KMS Server':
                    answer = prompt([{'type': 'input','name': 'option','message': 'KMS Server (10.0.0.0:1688):', 'default' : ""}])
                    if answer["option"] == "":
                        self.kms_server = None
                    else:
                        self.kms_server = answer["option"]
                elif answer['option'] == 'Cancel':
                    return None
            except KeyboardInterrupt as e:
                return
            except Exception as e:
                print(str(e))
                pass


class ADOrganizationalUnit:
    def __init__(self, name, parent=None):
        self.ou = {}
        self.name = name
        self.groups = {}
        self.users = {}
        self.parent = parent
        self.parent_path = parent.path
        if  isinstance(parent, ADStructure):
            self.parent_path = None
        self.path = ""
        self.syn_path()
        self.account_generator = None
    
    def from_json(obj, parent=None):
        ret = ADOrganizationalUnit(obj["name"],parent)
        for name, ou in obj["ou"].items():
            parsed_ou = ADOrganizationalUnit.from_json(ou,ret)
            parsed_ou.name = name
            parsed_ou.parent = ret
            ret.ou[name] = parsed_ou
        
        for name, grp in obj["groups"].items():
            parsed_grp = ADGroup.from_json(grp,ret)
            parsed_grp.parent = ret
            ret.groups[name] = parsed_grp

        for name, grp in obj["users"].items():
            parsed_grp = ADUser.from_json(grp,ret)
            parsed_grp.parent = ret
            ret.users[name] = parsed_grp
        return ret
    
    
    def to_json(self, full=False):
        if full:
            ret = {
                'ou' : {},
                'groups' : {},
                'name' : self.name,
                'users' : {}
            }
            for name, ou in self.ou.items():
                ret['ou'][name] = ou.to_json(full=True)
            for name, grp in self.groups.items():
                ret['groups'][name] = grp.to_json()
            for name, usr in self.users.items():
                ret['users'][usr.account_name] = usr.to_json()
            return ret
        return { "name" : self.name, "path" : self.path, "parent_path" : self.parent_path}
    
    def tree_str(self,level=0):
        to_join = ["{}>{}".format("  "*level, self.name)]
        for name, ou in self.ou.items():
            to_join.append(ou.tree_str(level=(level+1)))
        for name, grp in self.groups.items():
            to_join.append("{}>{} (Group)".format("  "*(level+1), grp.name))
        for name, usr in self.users.items():
            to_join.append("{}>{} (User)".format("  "*(level+1), usr.account_name))
        return "\n".join(to_join)

    def get_password_generator(self):
        if self.parent:
            if hasattr(self.parent,'password_generator'):
                return self.parent.password_generator
            else:
                return self.parent.get_password_generator()
        else:
            if hasattr(self,'password_generator'):
                return self.password_generator
            else:
                return cancamusa_common.PASSWORD_GENERATOR_FIRSTNAME_YEAR


    def list_child_ou(self):
        ret = [self.to_json()]
        for name, ou in self.ou.items():
            ret = ret + ou.list_child_ou()
        return ret
    
    def list_groups(self):
        ret = []
        for name, ou in self.ou.items():
            ret = ret + ou.list_groups()
        for name, grp in self.groups.items():
            ret.append(grp.to_json())
        return ret

    def list_users(self):
        ret = []
        for name, ou in self.ou.items():
            ret = ret + ou.list_users()
        for name, grp in self.users.items():
            ret.append(grp.to_json())
        return ret

    def syn_path(self):
        self.parent_path = None
        self.path = ""
        if self.parent:
            self.path = "OU=" + self.name + "," + self.parent.path
            self.parent_path = self.parent.path
            if  isinstance(self.parent, ADStructure):
                self.parent_path = None
        for name, ou in self.ou.items():
            ou.syn_path()
        for name, grp in self.groups.items():
            grp.syn_path()

    def change_name(self,name):
        self.name = name
        self.syn_path()
    
    def edit_interactive(self):
        while True:
            try:
                options =  ['Edit name','Show path','Add OU','Import OUs', 'Add group', 'Import Groups','Add Users']
                if len(self.ou) > 0:
                    options.append('Show OUs')
                    options.append('Edit OU')
                    options.append('Delete OU')
                if len(self.groups) > 0:
                    options.append('Show Groups')
                    options.append('Edit Groups')
                    options.append('Delete Groups')
                if len(self.users) > 0:
                    options.append('Show Users')
                    options.append('Edit Users')
                    options.append('Delete Users')
                options.append('Back')
                options.append('Cancel')
                
                answer = prompt([{'type': 'list','name': 'option','message': "Editing {} OU".format(self.name), 'choices' : options}])
                if answer['option'] == 'Show OUs':
                    for ou_name in self.ou.keys():
                        print(ou_name)
                elif answer['option'] == 'Edit name':
                    answer = prompt([{'type': 'input','name': 'option','message': 'Group name:', 'default' : self.name}])
                    self.change_name(answer['option'])
                elif answer['option'] == 'Show path':
                    print(self.path)
                elif answer['option'] == 'Add OU':
                    answer = prompt([{'type': 'input','name': 'option','message': 'OU name:', 'default' : ""}])
                    ou = ADOrganizationalUnit(answer['option'],self)
                    ou.account_generator = self.account_generator
                    ou = ou.edit_interactive()
                    if ou:
                        self.ou[ou.name] = ou
                elif answer['option'] == 'Edit OU':
                    answer = prompt([{'type': 'list','name': 'option','message': 'Select a OU to edit', 'choices' :self.ou.keys()}])
                    self.ou[answer['option']].account_generator = self.account_generator
                    self.ou[answer['option']].edit_interactive()
                elif answer['option'] == 'Delete OU':
                    answer = prompt([{'type': 'list','name': 'option','message': 'Select a OU to delete', 'choices' :self.ou.keys()}])
                    self.ou.pop(answer["option"], None)

                elif answer['option'] == 'Show Groups':
                    for ou_name in self.groups.keys():
                        print(ou_name)
                elif answer['option'] == 'Add Groups':
                    answer = prompt([{'type': 'input','name': 'option','message': 'Group name:', 'default' : ""}])
                    grp = ADGroup(self,answer["option"],answer["option"],answer["option"])
                    grp = grp.edit_interactive()
                    if grp:
                        self.groups[grp.name] = grp
                elif answer['option'] == 'Edit Groups':
                    answer = prompt([{'type': 'list','name': 'option','message': 'Select a Group to edit', 'choices' :self.groups.keys()}])
                    self.groups[answer['option']].edit_interactive()
                elif answer['option'] == 'Delete Groups':
                    answer = prompt([{'type': 'list','name': 'option','message': 'Select a Group to delete', 'choices' :self.groups.keys()}])
                    self.groups.pop(answer["option"], None)
                
                elif answer['option'] == 'Add Users':
                    answer = prompt([{'type': 'input','name': 'option','message': 'User name:', 'default' : ""}])
                    grp = ADUser(self,answer["option"],"","",answer["option"],"","",self.account_generator)
                    grp = grp.edit_interactive()
                    if grp:
                        self.users[grp.account_name] = grp
                elif answer['option'] == 'Show Users':
                    for ou_name in self.users.keys():
                        print(ou_name)
                elif answer['option'] == 'Edit Users':
                    answer = prompt([{'type': 'list','name': 'option','message': 'Select a User to edit', 'choices' :self.users.keys()}])
                    self.users[answer['option']].edit_interactive()
                elif answer['option'] == 'Delete Users':
                    answer = prompt([{'type': 'list','name': 'option','message': 'Select a User to delete', 'choices' :self.users.keys()}])
                    self.users.pop(answer["option"], None)
                elif answer['option'] == 'Back':
                    return self
                elif answer['option'] == 'Cancel':
                    return None
            except KeyboardInterrupt as e:
                return
            except Exception as e:
                pass

class ADGroup:
    def __init__(self, parent, name, sam_account_name,display_name, group_category="Security",group_scope="Global"):
        self.parent = parent
        self.name = name
        self.sam_account_name = sam_account_name
        self.display_name = display_name
        self.group_category = group_category
        self.group_scope = group_scope
        self.path = ""
        if parent:
            self.path = parent.path
    
    def from_json(obj,parent=None):
        return ADGroup(parent,obj["name"],obj["sam_account_name"],obj["display_name"],obj["group_category"],obj["group_scope"])

    def to_json(self):
        return { 
            "name" : self.name, 
            "sam_account_name" : self.sam_account_name,
            "display_name" : self.display_name,
            "group_category" : self.group_category,
            "group_scope" : self.group_scope,
            "path" : self.path
        }
    
    def syn_path(self):
        self.path = ""
        if self.parent:
            self.path = self.parent.path

    def create_interactive(parent=None):
        grp = ADGroup(parent,"","","")
        grp = grp.edit_interactive()
        return grp
    
    def edit_interactive(self):
        property_names = list(map(lambda x: str(x),dir(self)))
        class_props =  list(map(lambda x: str(x),dir(ADGroup)))
        for element in class_props:
            property_names.pop(property_names.index(element))

        for prop in property_names:
            if prop.startswith("_") or prop == 'parent' or prop == 'path':
                continue
            answer = prompt([{'type': 'input','name': 'option','message': "Editing {} Group".format(prop), 'default' :str(getattr(self,prop))}])
            setattr(self,prop,answer['option'])
        return self


class ADUser:
    def __init__(self, parent, first_name,second_name, account_name,display_name, password,department, account_generator=None):
        self.parent = parent
        self.first_name = first_name
        self.second_name = second_name
        if account_generator != None and ' ' in first_name:
            self.account_name = cancamusa_common.generate_account_name(first_name, account_generator)
        else:  
            self.account_name = account_name
        self.display_name = display_name
        self.password = password
        self.department = department
        self.path = ""
        if parent:
            self.path = parent.path
    
    def from_json(obj,parent=None):
        return ADUser(parent,obj["first_name"],obj["second_name"],obj["account_name"],obj["display_name"],obj["password"],obj["department"])

    def to_json(self):
        return { 
            "first_name" : self.first_name, 
            "second_name" : self.second_name,
            "account_name" : self.account_name,
            "display_name" : self.display_name,
            "password" : self.password,
            "path" : self.path,
            "department" : self.department
        }
    
    def syn_path(self):
        self.path = ""
        if self.parent:
            self.path = self.parent.path

    def create_interactive(parent=None):
        grp = ADUser(parent,"","","","","","")
        grp = grp.edit_interactive()
        return grp
    
    def edit_interactive(self):
        property_names = list(map(lambda x: str(x),dir(self)))
        class_props =  list(map(lambda x: str(x),dir(ADUser)))
        for element in class_props:
            property_names.pop(property_names.index(element))
        property_names.remove("password")
        property_names.append("password")
        for prop in property_names:
            if prop.startswith("_") or prop == 'parent' or prop == 'path':
                continue
            if prop == 'password' and self.parent:
                pass_gen = self.parent.get_password_generator()
                if pass_gen == cancamusa_common.PASSWORD_GENERATOR_FIRSTNAME_YEAR:
                    self.password = self.first_name + str(date.today().year)
                elif pass_gen == cancamusa_common.PASSWORD_GENERATOR_USERNAME_YEAR:
                    self.password = self.account_name + str(date.today().year)
                elif pass_gen == cancamusa_common.PASSWORD_GENERATOR_FIRST_LAST_YEAR:
                    self.password = self.first_name + self.second_name + str(date.today().year)
            answer = prompt([{'type': 'input','name': 'option','message': "Editing {}".format(prop), 'default' :str(getattr(self,prop))}])
            setattr(self,prop,answer['option'])
        return self