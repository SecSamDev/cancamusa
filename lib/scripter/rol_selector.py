from jinja2 import Template
import os
import ipaddress

ROLE_DOMAIN_CONTROLLER = 'DC'
ROLE_EXCHANGE = 'Exchange'
ROLE_WEB_SERVER = 'Web Server'
ROLE_AD_FOREST = 'AD Forest'
ROLE_DHCP = 'DHCP'
ROLE_DNS = 'DNS'
ROLE_KMS = 'KMS'



AVAILABLE_ROLES = [ROLE_DOMAIN_CONTROLLER, ROLE_WEB_SERVER, ROLE_EXCHANGE, ROLE_AD_FOREST, ROLE_DHCP,ROLE_DNS, ROLE_KMS]

def generate_rol_files_for_host(host,builder, project):
    print("Generating role files for {}".format(host.computer_name))
    project_path = os.path.join(project.config_path, "build")
    host_path = os.path.join(project_path, host.computer_name)
    if len(host.roles.roles) > 0:
        selected_roles = set(host.roles.roles)
        if ROLE_DHCP in selected_roles:
            generate_files_for_DHCP(host,builder, project)
        if ROLE_DNS in selected_roles:
            generate_files_for_DNS(host,builder, project)
        if ROLE_DOMAIN_CONTROLLER in selected_roles:
            generate_files_for_DC(host,builder,project)
        if ROLE_WEB_SERVER in selected_roles:
            generate_files_for_WS(host,builder,project)
        if ROLE_KMS in selected_roles:
            generate_files_for_KMS(host,builder,project)

def generate_files_for_DC(host,builder, project):
    # Create DOMAIN
    domain = project.domain
    project_path = os.path.join(project.config_path, "build")
    host_path = os.path.join(project_path, host.computer_name)
    actual_domain = None
    for dmn in domain.domains:
        if dmn.domain == host.domain:
            actual_domain = dmn
            break
    if actual_domain == None:
        print("Domain not found for host: " + str(host.computer_name))
        return
    
    
    primary_dc = project.primary_dc_config()
    config = project.dc_servers[host.computer_name]
    config['admin_user'] = actual_domain.default_admin
    config['admin_password'] = actual_domain.default_admin_password
    domain_ip = host.networks[0].ip_address[0]
    domain_name = actual_domain.domain
    domain_netbios = actual_domain.name
    domain_subnet = host.networks[0].ip_subnet[0]
    dns1 = project.primary_dns_config()
    dns1 = dns1['ip'] if dns1 != None else '8.8.8.8'
    dns2 = '127.0.0.1'
    with open(os.path.join(os.path.dirname(__file__), 'templates', host.os.win_type, 'create-domain.ps1.jinja'), 'r') as file_r:
        template = Template(file_r.read())
        actual_file_out_path = os.path.join(host_path,'iso_file', 'create-domain.ps1')
        with open(actual_file_out_path, 'w') as file_w:
            file_w.write(template.render(domain_ip=domain_ip,domain_subnet=domain_subnet, domain_name=domain_name, domain_netbios= domain_netbios,primary_dc=primary_dc,config=config,dns1=dns1,dns2=dns2))
        builder.add_script(actual_file_out_path)

    ad_groups = actual_domain.list_groups()
    ad_ous = actual_domain.list_child_ou()
    user_list = actual_domain.list_users()
    with open(os.path.join(os.path.dirname(__file__), 'templates', host.os.win_type, 'fill-ad.ps1.jinja'), 'r') as file_r:
        template = Template(file_r.read())
        actual_file_out_path = os.path.join(host_path,'iso_file', 'fill-ad.ps1')
        with open(actual_file_out_path, 'w') as file_w:
            file_w.write(template.render(user_list=user_list, ad_groups=ad_groups, ad_ous=ad_ous, domain=actual_domain.domain))
        builder.add_config(actual_file_out_path)
    

def generate_files_for_WS(host,builder, project):
    project_path = os.path.join(project.config_path, "build")
    host_path = os.path.join(project_path, host.computer_name)
    with open(os.path.join(os.path.dirname(__file__), 'templates', host.os.win_type, 'install-iis.ps1.jinja'), 'r') as file_r:
        template = Template(file_r.read())
        actual_file_out_path = os.path.join(host_path,'iso_file', 'install-iis.ps1')
        with open(actual_file_out_path, 'w') as file_w:
            file_w.write(template.render())
        builder.add_script(actual_file_out_path)

def generate_files_for_DHCP(host,builder, project):
    project_path = os.path.join(project.config_path, "build")
    host_path = os.path.join(project_path, host.computer_name)
    # Create DHCP files
    # Scopes
    scopes = []
    dns_server = project.dns_servers[host.computer_name] if host.computer_name in project.dns_servers else None
    fixed_ips = []
    for network in project.networks:
        net = ipaddress.ip_network(network,False)
        usable_host = list(net.hosts())
        exclusions = []
        for excluded_ip in project.fixed_ips:
            excluded_net = ipaddress.ip_network(excluded_ip,False)
            if excluded_net.network_address != net.network_address:
                continue
            excluded_ip = excluded_ip.split("/")[0]
            fixed_ips.append(excluded_ip)
            exclusions.append(excluded_ip)
        scopes.append({
            "name" : "Network {}".format(network),
            "start_range" : str(usable_host[0]),
            "end_range" : str(usable_host[-1]),
            "subnet_mask" : str(net.netmask),
            "scope_id" : str(net.network_address),
            "exclusions" : exclusions
        })
    domain = project.domain.get_domain(host.domain)
    dhcp_config = project.dhcp_servers[host.computer_name]
    with open(os.path.join(os.path.dirname(__file__), 'templates', host.os.win_type, 'install-dhcp.ps1.jinja'), 'r') as file_r:
        template = Template(file_r.read())
        actual_file_out_path = os.path.join(host_path,'iso_file', 'install-dhcp.ps1')
        with open(actual_file_out_path, 'w') as file_w:
            file_w.write(template.render(host=host, dmn=domain, dns=dns_server, scopes=scopes, config=dhcp_config))
        builder.add_script(actual_file_out_path)
    
    fixed_hosts = []
    for hst in project.hosts:
        if host.networks[0].ip_address[0] in fixed_ips:
            fixed_hosts.append(hst)

    with open(os.path.join(os.path.dirname(__file__), 'templates', host.os.win_type, 'fill-dhcp.ps1.jinja'), 'r') as file_r:
        template = Template(file_r.read())
        actual_file_out_path = os.path.join(host_path,'iso_file', 'fill-dhcp.ps1')
        with open(actual_file_out_path, 'w') as file_w:
            file_w.write(template.render(thishost=host, dmn=domain, hosts=fixed_hosts, config=dhcp_config))
        thishost = None
        builder.add_script(actual_file_out_path)

def generate_files_for_KMS(host,builder, project):
    project_path = os.path.join(project.config_path, "build")
    host_path = os.path.join(project_path, host.computer_name)
    with open(os.path.join(os.path.dirname(__file__), 'templates', host.os.win_type, 'install-kms.ps1.jinja'), 'r') as file_r:
        template = Template(file_r.read())
        actual_file_out_path = os.path.join(host_path,'iso_file', 'install-kms.ps1')
        with open(actual_file_out_path, 'w') as file_w:
            file_w.write(template.render())
        builder.add_script(actual_file_out_path)

def generate_files_for_DNS(host,builder, project):
    # Create DNS files
    project_path = os.path.join(project.config_path, "build")
    host_path = os.path.join(project_path, host.computer_name)
    dns_server = project.dns_servers[host.computer_name]
    with open(os.path.join(os.path.dirname(__file__), 'templates', host.os.win_type, 'install-dns.ps1.jinja'), 'r') as file_r:
        template = Template(file_r.read())
        actual_file_out_path = os.path.join(host_path,'iso_file', 'install-dns.ps1')
        with open(actual_file_out_path, 'w') as file_w:
            file_w.write(template.render(dns=dns_server))
        builder.add_script(actual_file_out_path)
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
            elif rol['Name'] == 'Web-Server':
                returned_roles.append(ROLE_WEB_SERVER)
            elif rol['Name'] == 'VolumeActivation':
                returned_roles.append(ROLE_KMS)
    
    if 'AD-Domain-Services' in detected_roles:
        if 'RSAT-AD-AdminCenter' in detected_roles:
            returned_roles.append(ROLE_DOMAIN_CONTROLLER)
        else:
            returned_roles.append(ROLE_AD_FOREST)
    

    return list(set(returned_roles))

def calculate_dhcp_failover(host1, host2):
    if host1.domain == None or host1.domain == "" or host2.domain == None or host2.domain == "" or host1.domain != host2.domain:
        return None
    config = host1.roles.config[ROLE_DHCP]
    
    scopes1 = set()
    scopes2 = set()
    for netw in host1.networks:
        net = ipaddress.ork("{}/{}".format(netw.ip_address[0], netw.ip_subnet[0]),False)
        scopes1.add(str(net.network_address))
    for netw in host2.networks:
        net = ipaddress.ip_network("{}/{}".format(netw.ip_address[0], netw.ip_subnet[0]),False)
        scopes2.add(str(net.network_address))
    common_scopes = list(scopes1.intersection(scopes2))

    return {
        'partner' : "{}.{}".format(host2.computer_name,host2.domain),
        'scopes' : common_scopes,
        'scopes_ids' : ",".join(common_scopes),
        'name' : "{}-{}".format(host1.computer_name,host2.computer_name),
        'mode' : config['failover_mode'],
        'secret': config['failover_secret'] if 'failover_secret' in config else ""
    }