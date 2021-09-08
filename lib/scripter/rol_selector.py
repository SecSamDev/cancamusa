from jinja2 import Template
import os

ROLE_DOMAIN_CONTROLLER = 'DC'
ROLE_EXCHANGE = 'Exchange'
ROLE_WEB_SERVER = 'Web Server'
ROLE_AD_FOREST = 'AD Forest'
ROLE_DHCP = 'DHCP'
ROLE_DNS = 'DNS'



AVAILABLE_ROLES = [ROLE_DOMAIN_CONTROLLER, ROLE_WEB_SERVER, ROLE_EXCHANGE, ROLE_AD_FOREST, ROLE_DHCP,ROLE_DNS]

def generate_rol_files_for_host(host,builder, project):
    print("Generating role files for {}".format(host.computer_name))
    project_path = os.path.join(project.config_path, "build")
    host_path = os.path.join(project_path, host.computer_name)
    if len(host.roles.roles) > 0:
        selected_roles = set(host.roles.roles)
        if ROLE_DHCP in selected_roles:
            generate_files_for_DHCP(host,builder,host_path)
        if ROLE_DNS in selected_roles:
            generate_files_for_DHCP(host,builder,host_path)
        if ROLE_DOMAIN_CONTROLLER in selected_roles:
            generate_files_for_DC(host,project.domain,builder,host_path)
        if ROLE_WEB_SERVER in selected_roles:
            generate_files_for_WS(host,builder,host_path)

def generate_files_for_DC(host,domain,builder, host_path):
    # Create DOMAIN
    actual_domain = None
    for dmn in domain.domains:
        if dmn.name == host.domain:
            actual_domain = dmn
    if actual_domain == None:
        print("Domain not found....")
        print(actual_domain)
        return
    ad_groups = actual_domain.list_groups()
    ad_ous = actual_domain.list_child_ou()
    user_list = actual_domain.list_users()
    with open(os.path.join(os.path.dirname(__file__), 'scripter', 'templates', host.os.win_type, 'create-domain.ps1.jinja'), 'r') as file_r:
        template = Template(file_r.read())
        actual_file_out_path = os.path.join(host_path,'iso_file', 'create-domain.ps1')
        with open(actual_file_out_path, 'w') as file_w:
            file_w.write(template.render(user_list=user_list, ad_groups=ad_groups, ad_ous= ad_ous))
        builder.add_script(actual_file_out_path)
    

def generate_files_for_WS(host,builder, host_path):
    with open(os.path.join(os.path.dirname(__file__), 'scripter', 'templates', host.os.win_type, 'install-iis.ps1.jinja'), 'r') as file_r:
        template = Template(file_r.read())
        actual_file_out_path = os.path.join(host_path,'iso_file', 'install-iis.ps1')
        with open(actual_file_out_path, 'w') as file_w:
            file_w.write(template.render())
        builder.add_script(actual_file_out_path)

def generate_files_for_DHCP(host,builder, host_path):
    # Create DHCP files
    pass

def generate_files_for_DNS(host,builder, host_path):
    # Create DNS files
    pass


def roles_from_extracted_info(roles):
    returned_roles = []
    detected_roles = set()
    for rol in roles:
        if 'Name' in rol:
            detected_roles.add(rol['Name'])
            if rol['Name'] == 'DHCP':
                returned_roles.append(ROLE_DHCP)
            elif rol['Name'] == 'DNS':
                returned_roles.append(ROLE_DNS)
            elif rol['Name'] == 'Web-Server':
                returned_roles.append(ROLE_WEB_SERVER)
    
    if 'AD-Domain-Services' in detected_roles:
        if 'RSAT-AD-AdminCenter' in detected_roles:
            returned_roles.append(ROLE_DOMAIN_CONTROLLER)
        else:
            returned_roles.append(ROLE_AD_FOREST)
    

    return returned_roles