from PyInquirer import prompt
import cancamusa_common

class CancamusaDomain:
    def __init__(self, domains=[]):
        self.domains = domains
    
    def load_from_object(obj):
        domains = []
        for dmn in obj["domains"]:
            domain = ADStructure.from_json(dmn)
            domains.append(domain)
        cancamusa = CancamusaDomain(domains)
        return cancamusa

    def add_domain(self,domain):
        self.domains.append(domain)

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
                    domain = ADStructure(answer['option'])
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
    def __init__(self, domain):
        self.ou = {}
        self.domain = domain
        dc_path_string = "DC=" + (",DC=".join(domain.split(".")))
        self.path = dc_path_string
        self.default_local_admin = 'LocalAdmin'
        self.account_generator = cancamusa_common.ACCOUNT_FORMAT_NAME_DOT_SURNAME
    
    def from_json(obj):
        ret = ADStructure(obj["domain"])
        for name, ou in obj["ou"].items():
            parsed_ou = ADOrganizationalUnit.from_json(ou,parent=ret)
            ret.ou[parsed_ou.name] = parsed_ou
        if 'default_local_admin' in obj:
            ret.default_local_admin = obj['default_local_admin']
        if 'account_generator' in obj:
            ret.account_generator = obj['account_generator']
        return ret

    def __str__(self):
        return "{} : {}".format(self.domain, self.path)

    def to_json(self):
        ret = {
            'ou' : {},
            'domain' : self.domain,
            'default_local_admin' : self.default_local_admin
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

    def edit_interactive(self):
        while True:
            try:
                options =  ['Add OU','Import OUs']
                if len(self.ou) > 0:
                    options.append('Show OUs')
                    options.append('Show OU Tree')
                    options.append('Edit OU')
                    options.append('Delete OU')
                options.append('Account Generator')
                options.append('Default Local Admin')
                options.append('Back')
                options.append('Cancel')
                answer = prompt([{'type': 'list','name': 'option','message': 'OrganizationalUnit edition mode', 'choices' : options}])
                if answer['option'] == 'Show OUs':
                    for ou_name in self.ou.keys():
                        print(ou_name)
                if answer['option'] == 'Show OU Tree':
                    for ou_name, ou in self.ou.items():
                        print(ou.tree_str())
                elif answer['option'] == 'Add OU':
                    answer = prompt([{'type': 'input','name': 'option','message': 'OU name:', 'default' : "CancamusaLab"}])
                    ou = ADOrganizationalUnit(answer['option'],self)
                    ou = ou.edit_interactive()
                    if ou:
                        self.ou[ou.name] = ou
                elif answer['option'] == 'Edit OU':
                    answer = prompt([{'type': 'list','name': 'option','message': 'Select a OU to edit', 'choices' :self.ou.keys()}])
                    self.ou[answer['option']].edit_interactive()
                elif answer['option'] == 'Account Generator':
                    answers = prompt([{'type': 'list','name': 'selection','message': 'Method used to generate random accounts. Ex: ' + cancamusa_common.ACCOUNT_FORMAT_EXAMPLE, 'choices' : [cancamusa_common.ACCOUNT_FORMAT_LETTER_SURNAME, cancamusa_common.ACCOUNT_FORMAT_NAME_DOT_SURNAME, cancamusa_common.ACCOUNT_FORMAT_TRHEE_LETTERS]}])
                    self.account_generator = answers['selection']
                elif answer['option'] == 'Default Local Admin':
                    answer = prompt([{'type': 'input','name': 'option','message': 'OU name:', 'default' : self.default_local_admin}])
                    self.default_local_admin = answer["option"]
                elif answer['option'] == 'Delete OU':
                    answer = prompt([{'type': 'list','name': 'option','message': 'Select a OU to delete', 'choices' :self.ou.keys()}])
                    self.ou.pop(answer["option"], None)
                elif answer['option'] == 'Back':
                    return self
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
        self.parent = parent
        self.parent_path = parent.path
        if  isinstance(parent, ADStructure):
            self.parent_path = None
        self.path = ""
        self.syn_path()
    
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
        return ret
    
    def to_json(self, full=False):
        if full:
            ret = {
                'ou' : {},
                'groups' : {},
                'name' : self.name
            }
            for name, ou in self.ou.items():
                ret['ou'][name] = ou.to_json(full=True)
            for name, grp in self.groups.items():
                ret['groups'][name] = grp.to_json()
            return ret
        return { "name" : self.name, "path" : self.path, "parent_path" : self.parent_path}
    
    def tree_str(self,level=0):
        to_join = ["{}>{}".format("  "*level, self.name)]
        for name, ou in self.ou.items():
            to_join.append(ou.tree_str(level=(level+1)))
        return "\n".join(to_join)

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
                options =  ['Edit name','Show path','Add OU','Import OUs', 'Add group', 'Import Groups']
                if len(self.ou) > 0:
                    options.append('Show OUs')
                    options.append('Edit OU')
                    options.append('Delete OU')
                if len(self.groups) > 0:
                    options.append('Show Groups')
                    options.append('Edit Groups')
                    options.append('Delete Groups')
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
                    answer = prompt([{'type': 'input','name': 'option','message': 'OU name:', 'default' : "CancamusaLab"}])
                    ou = ADOrganizationalUnit(answer['option'],self)
                    ou = ou.edit_interactive()
                    if ou:
                        self.ou[ou.name] = ou
                elif answer['option'] == 'Edit OU':
                    answer = prompt([{'type': 'list','name': 'option','message': 'Select a OU to edit', 'choices' :self.ou.keys()}])
                    self.ou[answer['option']].edit_interactive()
                elif answer['option'] == 'Delete OU':
                    answer = prompt([{'type': 'list','name': 'option','message': 'Select a OU to delete', 'choices' :self.ou.keys()}])
                    self.ou.pop(answer["option"], None)

                elif answer['option'] == 'Show Groups':
                    for ou_name in self.groups.keys():
                        print(ou_name)
                elif answer['option'] == 'Add Groups':
                    answer = prompt([{'type': 'input','name': 'option','message': 'Group name:', 'default' : "CancamusaGroup"}])
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

                elif answer['option'] == 'Back':
                    return self
                elif answer['option'] == 'Cancel':
                    return None
            except KeyboardInterrupt as e:
                return
            except:
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
        grp = ADGroup(parent,"CancamusaGroup","CancamusaGroup","Cancamusa Group")
        grp = grp.edit_interactive()
        return grp
    
    def edit_interactive(self):
        property_names = list(map(lambda x: str(x),dir(self)))
        class_props =  list(map(lambda x: str(x),dir(ADGroup)))
        for element in class_props:
            property_names.pop(property_names.index(element))

        for prop in property_names:
            if prop.startswith("_"):
                continue
            answer = prompt([{'type': 'input','name': 'option','message': "Editing {} Group".format(self.name), 'default' :str(getattr(self,prop))}])
            setattr(self,prop,answer['option'])
        return self