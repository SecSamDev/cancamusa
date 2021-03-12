
class ADStructure:
    def __init__(self, domain):
        self.ou = {}
        self.domain = domain
        dc_path_string = "DC=" + (",DC=".join(domain.split(".")))
        self.path = dc_path_string
    
    def from_json(obj):
        ret = ADStructure(obj["domain"])
        for name, ou in obj["ou"].items():
            parsed_ou = ADOrganizationalUnit.from_json(ou,parent=ret)
            ret.ou[parsed_ou.name] = parsed_ou
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
        if parent:
            self.path = "OU=" + name + "," + parent.path
    
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
    
    def to_json(self):
        return { "name" : self.name, "path" : self.path, "parent_path" : self.parent_path}

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

class ADGroup:
    def __init__(self, parent, name, sam_account_name,display_name, group_category="Security",group_scope="Global"):
        self.ou = {}
        self.groups = {}
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