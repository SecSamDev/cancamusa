import os
import json
import ipaddress
import errno
import requests
from PyInquirer import prompt

import cancamusa_common
from lib.host.host import HostInfo
from lib.domain import CancamusaDomain
from lib.host.builder import WindowsHostBuilder
from proxmox_deploy import ProxmoxDeployer
from lib.scripter.rol_selector import ROLE_DOMAIN_CONTROLLER, ROLE_DNS, ROLE_KMS, ROLE_WEB_SERVER, ROLE_DHCP, calculate_dhcp_failover
from configuration import CancamusaConfiguration



class CancamusaProject:
    """ Loads and stores information about a Cancamusa project """
    def __init__(self, config_path):
        self.project_name = "Cancamusa"
        self.description = "A simple lab project"
        self.config_path = config_path
        global_config = CancamusaConfiguration.load_or_create(None)
        self.config = {
            'siem' : {},
            'account_generator' : cancamusa_common.ACCOUNT_FORMAT_NAME_DOT_SURNAME,
            'language' : 'en',
            'admin_password' : 'CancamusaRocks123!',
            'password_generator' : cancamusa_common.PASSWORD_GENERATOR_FIRSTNAME_YEAR,
            'ssh' : {
                'enabled' : False,
                'copy_public_key' : False
            },
            "start_vmbr" : global_config.start_vmbr,
            "logos" : [],
            "oem" : {
                'Logo' : None,
                'Manufacturer' : 'CancamusaLabs',
                'Support Phone' : '+00 123456789',
                'Support URL' : 'http://support.com',
                'Support App URL' : 'mailto://support@cancamusa.com',
                'Model' : 'HidenLab'
            },
            "scripts" : [],
            "default_scripts" : []
        }
        self.domain = CancamusaDomain([],default_admin_password=self.config['admin_password'],password_generator=self.config['password_generator'])
        # QEMU machine ID
        self.host_id_start = 1000
        self.host_id_counter = 1000
        self.hosts = []
        # Project metadata updated
        self.networks = set()
        self.fixed_ips = set()
        self.dns_servers = {}
        self.dc_servers = {}
        self.dhcp_servers = {}
        self.kms_servers = {}
        self.iis_servers = {}
    
    def scan_hosts(self):
        found_dc = None
        found_dns = None
        found_dhcp = None
        found_iis = None
        found_kms = None
        for host in self.hosts:
            for netw in host.networks:
                # For simplicity use only the first IP of the list (IPV4)
                self.networks.add(str(ipaddress.ip_network('{}/{}'.format(netw.ip_address[0],netw.ip_subnet[0]),False)))
                if netw.assign_method == 'static' or netw.assign_method == 'fixed':
                    self.fixed_ips.add('{}/{}'.format(netw.ip_address[0],netw.ip_subnet[0]))
            if ROLE_DNS in host.roles.roles:
                # DNS server
                self.dns_servers[host.computer_name] = host.roles.config[ROLE_DNS]
                self.dns_servers[host.computer_name]['ip'] = host.networks[0].ip_address[0]
                self.dns_servers[host.computer_name]['primary'] = (found_dns == None)
                if found_dns == None:
                    found_dns = host
            if ROLE_KMS in host.roles.roles:
                # KMS server
                self.kms_servers[host.computer_name] = host.roles.config[ROLE_KMS]
                self.kms_servers[host.computer_name]['ip'] = host.networks[0].ip_address[0]
                self.kms_servers[host.computer_name]['primary'] = (found_kms == None)
                if found_kms == None:
                    found_kms = host
            if ROLE_WEB_SERVER in host.roles.roles:
                # KMS server
                self.iis_servers[host.computer_name] = host.roles.config[ROLE_KMS]
                self.iis_servers[host.computer_name]['ip'] = host.networks[0].ip_address[0]
                self.iis_servers[host.computer_name]['primary'] = (found_iis == None)
                if found_iis == None:
                    found_iis = host
            if ROLE_DOMAIN_CONTROLLER in host.roles.roles:
                # DC server
                self.dc_servers[host.computer_name] = host.roles.config[ROLE_DOMAIN_CONTROLLER]
                self.dc_servers[host.computer_name]['ip'] = host.networks[0].ip_address[0]
                self.dc_servers[host.computer_name]['primary'] = (found_dc == None)
                if found_dc == None:
                    found_dc = host
            if ROLE_DHCP in host.roles.roles:
                # DC server
                self.dhcp_servers[host.computer_name] = host.roles.config[ROLE_DHCP]
                self.dhcp_servers[host.computer_name]['ip'] = host.networks[0].ip_address[0]
                self.dhcp_servers[host.computer_name]['primary'] = (found_dhcp == None)
                if found_dhcp == None:
                    found_dhcp = host
                else:
                    # Configure failover
                    dhcp_server = self.dhcp_servers[found_dhcp.computer_name]
                    if not 'failovers' in dhcp_server:
                        dhcp_server['failovers'] = []
                    else:
                        failover = calculate_dhcp_failover(found_dhcp, host)
                        if failover != None:
                            failover_names = list(map(lambda x: x['name'], dhcp_server['failovers']))
                            if not failover['name'] in failover_names:
                                dhcp_server['failovers'].append(failover)

    def primary_dns_config(self):
        for key, srv in self.dns_servers.items():
            if srv['primary']:
                return srv
        return None
    
    def primary_kms_config(self):
        for key, srv in self.kms_servers.items():
            if srv['primary']:
                return srv
        return None
    
    def primary_dc_config(self):
        for key, srv in self.dc_servers.items():
            if srv['primary']:
                return srv
        return None
    
    def primary_dhcp_config(self):
        for key, srv in self.dhcp_servers.items():
            if srv['primary']:
                return srv
        return None

    def change_host_id_start(self, new_value):
        start_dif = new_value - self.host_id_start
        self.host_id_counter = self.host_id_counter + start_dif
        self.host_id_start = new_value
        for host in self.hosts:
            host.host_id = host.host_id + start_dif
    

    def add_host(self,host):
        # Do validation/transformation
        host.host_id = self.host_id_counter
        self.hosts.append(host)
        self.host_id_counter = self.host_id_counter + 1
        return self

    def save(self):
        if not self.config_path:
            raise Exception("Invalid config file path")
        if os.path.exists(os.path.join(self.config_path,'cancamusa.json.bckp')):
            raise Exception("There is an old backup file!")
        with open(os.path.join(self.config_path,'cancamusa.json.bckp'), 'w') as config_file_backup:
            with open(os.path.join(self.config_path,'cancamusa.json'), 'r') as config_file:
                config_file_backup.write(config_file.read())
        to_write = {
            'project_name' : self.project_name,
            'description' : self.description,
            'config' : self.config,
            'hosts' : [],
            'domain' : self.domain.to_json(),
            'host_id_counter' : self.host_id_counter,
            'host_id_start' : self.host_id_start
        }
        for host in self.hosts:
            host = host.to_json()
            if not 'host_id' in host:
                host['host_id'] = self.host_id_counter
                self.host_id_counter = self.host_id_counter + 1
            to_write['hosts'].append(host)
        config_json = json.dumps(to_write,indent=4,) 
        with open(os.path.join(self.config_path,'cancamusa.json'), 'w') as config_file:
            config_file.write(config_json)
        os.remove(os.path.join(self.config_path,'cancamusa.json.bckp'))
        return self

    def load_from_object(obj):
        cancamusa = CancamusaProject(None)
        cancamusa.project_name = obj['project_name']
        cancamusa.description = obj['description']
        for key in obj['config']:
            cancamusa.config[key] = obj['config'][key]
        cancamusa.hosts = []
        cancamusa.domain = CancamusaDomain.load_from_object(obj['domain'])
        cancamusa.domain.default_admin_password=cancamusa.config['admin_password']
        cancamusa.domain.password_generator=cancamusa.config['password_generator']
        cancamusa.host_id_start = int(obj['host_id_start']) if 'host_id_start' in obj else 1000
        cancamusa.host_id_counter = int(obj['host_id_counter']) if 'host_id_counter' in obj else cancamusa.host_id_start
        for host in obj['hosts']:
            cancamusa.hosts.append(HostInfo.from_json(host))
        cancamusa.scan_hosts()
        return cancamusa

    def set_elasticsearch_siem(self, host, security):
        self.config['siem']['elasticsearch'] = {
            'host' : host,
            'kibana' : ""
        }
        if security:
            self.config['siem']['elasticsearch']['security'] = security
        return self

    def set_sysmon_conf(self, conf_path):
        self.config['sysmon'] = {
            'conf' : conf_path,
            'driver' : 'UsbDrivr',
            'altitude' : 385202,
            'description' : "USB Driver",
            'download' : "https://download.sysinternals.com/files/Sysmon.zip"
        }
        return self
    
    
    def get_winlogbeat_file_if_not_exists(self):
        if 'winlogbeat' in self.config:
            if not os.path.exists(os.path.join(self.config_path,cancamusa_common.WINLOGBEAT_CONFIG_FILE)):
                copy_config_file(self.config_path, self.config['winlogbeat']['conf'],cancamusa_common.WINLOGBEAT_CONFIG_FILE)
    
    def get_sysmon_file_if_not_exists(self):
        if 'sysmon' in self.config:
            if not os.path.exists(os.path.join(self.config_path,cancamusa_common.SYSMON_CONFIG_FILE)):
                copy_config_file(self.config_path, self.config['sysmon']['conf'],cancamusa_common.SYSMON_CONFIG_FILE)

    def set_logstash_siem(self, host):
        self.config['siem']['logstash'] = {
            'host' : host
        }
        return self
    
    def edit_logstash(self):
        answers = prompt([{'type': 'confirm','name': 'siem_logstash','message': 'Set Logstash as a SIEM?'}])
        if answers['siem_logstash']:
            answers = prompt([{'type': 'input','name': 'logstash_host','message': 'Logstash Host.', 'default':'192.168.100.100:5044'}])
            self.set_logstash_siem(answers['logstash_host'])
    
    def edit_winlogbeat(self):
        answers = prompt([{'type': 'confirm','name': 'winlog','message': 'Set Winlogbeat as a LOG shipper?'}])
        if not answers['winlog']:
            self.config.pop('winlogbeat',None)
            return
        answers = prompt([{'type': 'input','name': 'winlogbeat','message': 'WinLogBeat configuration file path'}])
        if not 'winlogbeat' in self.config:
            self.config['winlogbeat'] = {}
        if answers['winlogbeat'].strip() == "":
            print("Creating custom winlogbeat configuration file...")
            content = create_custom_winlogbeat_file(self)
            location = os.path.join(self.config_path,'config_files',cancamusa_common.WINLOGBEAT_CONFIG_FILE)
            with open(location, 'w') as write_file:
                write_file.write(content)
            self.config['winlogbeat']['conf'] = location
        else:
            copy_config_file(self.config_path,answers['winlogbeat'],cancamusa_common.WINLOGBEAT_CONFIG_FILE)
            self.config['winlogbeat']['conf'] = answers['winlogbeat']
        
        answers = prompt([{'type': 'input','name': 'winlogbeat','message': 'WinLogBeat Download URL:'}])
        if answers['winlogbeat'].strip() == "":
            self.config['winlogbeat']['download'] = "https://artifacts.elastic.co/downloads/beats/winlogbeat/winlogbeat-7.14.1-windows-x86_64.zip"
        else:
            self.config['winlogbeat']['download'] = answers['winlogbeat']

    def edit_elasticsearch(self):
        answers = prompt([{'type': 'confirm','name': 'siem_elastic','message': 'Select ElasticSearch as a SIEM?'}])
        if answers['siem_elastic']:
            answers = prompt([{'type': 'input','name': 'elastic_url','message': 'Elasticsearch Host.','default' : 'http://192.168.100.100:9200/elasticsearch'},{'type': 'list','name': 'elastic_security','message': 'Elasticsearch authentication mecanism', 'choices' : ["Basic","API key", "PKI certificate", "none"], 'value' : "none"}])
            if answers['elastic_security'] == 'Basic' :
                sec_answers = prompt([{'type': 'input','name': 'username','message': 'Elasticsearch username'},{'type': 'input','name': 'password','message': 'Elasticsearch password'}])
                self.set_elasticsearch_siem(answers['elastic_url'],{'username' : sec_answers['username'], 'password' : sec_answers['password']})
            elif answers['elastic_security'] == 'API key' :
                sec_answers = prompt([{'type': 'input','name': 'api_key','message': 'Elasticsearch API Key'}])
                self.set_elasticsearch_siem(answers['elastic_url'],{'api_key' : sec_answers['api_key']})
            elif answers['elastic_security'] == 'PKI certificate' :
                sec_answers = prompt([{'type': 'input','name': 'certificate','message': 'Absolute path to elasticsearch client PEM certificate'},{'type': 'input','name': 'key','message': 'Absolute path to elasticsearch client certificate key'}])
                self.set_elasticsearch_siem(answers['elastic_url'],{'certificate' : sec_answers['certificate'], 'key' : sec_answers['key']})
                copy_config_file(self.config_path,sec_answers['certificate'],cancamusa_common.ELASTIC_CERTIFICATE)
                copy_config_file(self.config_pathh,sec_answers['key'],cancamusa_common.ELASTIC_CERTIFICATE_KEY)
            else:
                self.set_elasticsearch_siem(answers['elastic_url'],None)
            answers = prompt([{'type': 'confirm','name': 'siem_elastic','message': 'Configure also Kibana?'}])
            if answers['siem_elastic']:
                answers = prompt([{'type': 'input','name': 'elastic_url','message': 'Kibana Host.','default' : 'http://192.168.100.100:5601'}])
                self.config['siem']['elasticsearch']['kibana'] = answers['elastic_url']
    
    def edit_socks_proxy(self):
        if not 'proxy' in self.config:
            answers = prompt([{'type': 'confirm','name': 'proxy','message': 'Use a SOCKS proxy?'}])
            if not answers['proxy']:
                self.config.pop('proxy',None)
                return
            self.config['proxy'] = {
                'ip' : "",
                'port' : 1080
            }
        answer = prompt([{'type': 'input','name': 'option','message': 'Proxy host (10.10.10.10):', 'default' : str(self.config['proxy']['ip'])}])
        description = answer['option']
        self.config['proxy']['ip'] = description
        answer = prompt([{'type': 'input','name': 'option','message': 'Proxy port (1080):', 'default' : str(self.config['proxy']['port'])}])
        description = int(answer['option'])
        self.config['proxy']['port'] = description
        answers = prompt([{'type': 'confirm','name': 'proxy','message': 'Use user+password?'}])
        if not answers['proxy']:
            self.config['proxy'].pop('username',None)
            self.config['proxy'].pop('password',None)
            return
        if not 'username' in self.config['proxy']:
            self.config['proxy']['username'] = "user"
            self.config['proxy']['password'] = "password"
        answer = prompt([{'type': 'input','name': 'option','message': 'Proxy username:', 'default' : self.config['proxy']['username']}])
        description = answer['option']
        self.config['proxy']['username'] = description
        answer = prompt([{'type': 'input','name': 'option','message': 'Proxy password:', 'default' : self.config['proxy']['password']}])
        description = int(answer['option'])
        self.config['proxy']['password'] = description


    def edit_sysmon(self):
        while True:
            if not 'sysmon' in self.config:
                answers = prompt([{'type': 'confirm','name': 'sysmon','message': 'Install Sysmon in each host?'}])
                if not answers['sysmon']:
                    self.config.pop('sysmon',None)
                    return
                self.config['sysmon'] = {
                    'conf' : "",
                    'driver' : 'USBDrvr',
                    'service' :'USBSrvc',
                    'altitude' : 385201,
                    'description' : "USB Service",
                    "download" : "https://download.sysinternals.com/files/Sysmon.zip"
                }
            answers = prompt([{'type': 'input','name': 'sysmon_conf','message': 'Sysmon configuration file path', 'default' : self.config['sysmon']['conf']}])
            if answers['sysmon_conf'] != self.config['sysmon']['conf']:
                self.set_sysmon_conf(answers['sysmon_conf'])
                copy_config_file(self.config_path,answers['sysmon_conf'],cancamusa_common.SYSMON_CONFIG_FILE)

            answer = prompt([{'type': 'input','name': 'option','message': 'Edit Sysmon Driver Name ([a-zA-Z]{8}):', 'default' : str(self.config['sysmon']['driver'])}])
            name = answer['option'][:8]# Only 8 characters
            self.config['sysmon']['driver'] = name.encode("ascii", "ignore").decode()
            
            if not 'service' in self.config['sysmon']:
                self.config['sysmon']['service'] = self.config['sysmon']['driver'][0:4] + "Srvc"
            answer = prompt([{'type': 'input','name': 'option','message': 'Edit Sysmon Service Name ([a-zA-Z]{8}):', 'default' : str(self.config['sysmon']['service'])}])
            name = answer['option'][:8]# Only 8 characters
            self.config['sysmon']['service'] = name.encode("ascii", "ignore").decode()

            if self.config['sysmon']['driver'] == self.config['sysmon']['service']:
                print('Sysmon driver and service must not be the same IDKW')
                continue

            answer = prompt([{'type': 'input','name': 'option','message': 'Edit Sysmon Driver Altitude:', 'default' : str(self.config['sysmon']['altitude'])}])
            self.config['sysmon']['altitude'] = int(answer['option'])
            
            answer = prompt([{'type': 'input','name': 'option','message': 'Edit Sysmon service Description:', 'default' : str(self.config['sysmon']['description'])}])
            self.config['sysmon']['description'] = answer['option']

            if not 'download' in self.config['sysmon']:
                self.config['sysmon']['download'] = "https://download.sysinternals.com/files/Sysmon.zip"

            answer = prompt([{'type': 'input','name': 'option','message': 'Set Sysmon download URL:', 'default' : self.config['sysmon']['download']}])
            self.config['sysmon']['download'] = answer['option']

            break


    def new_project_in_path(pth):
        cancamusa = CancamusaProject(pth)
        create_config_path_if_not_exists(pth)
        answers = prompt([{'type': 'input','name': 'project_name','message': 'Name of the project','default':os.path.basename(pth)},{'type': 'input','name': 'description','message': 'Description of the project','default':"Malware laboratory"}])
        cancamusa.project_name = answers['project_name']
        cancamusa.description = answers['description']
        # ---------- Install SIEMS ----------
        answers = prompt([{'type': 'confirm','name': 'wants_siem','message': 'Configure a SIEM to send Windows Logs?'}])
        if answers['wants_siem']:
            # ---------- ElasticSearch ----------
            cancamusa.edit_elasticsearch()
            # ---------- LOGSTASH ----------
            cancamusa.edit_logstash()
            # ---------- WinLogBeat ----------    
            cancamusa.edit_winlogbeat()
        
        # ---------- Sysmon ----------
        cancamusa.edit_sysmon()
        cancamusa.save()
        return cancamusa


    def edit_hosts(self):
        while True:
            options =  ['Add host','Import hosts','Edit QEMU start ID']
            if len(self.hosts) > 0:
                options.append('Show hosts')
                options.append('Edit host')
                options.append('Delete host')
            options.append('Back')
            answer = prompt([{'type': 'list','name': 'option','message': 'Host edition mode', 'choices' : options}])
            if answer['option'] == 'Show hosts':
                for host in self.hosts:
                    print(host.computer_name)

            if answer['option'] == 'Add host':
                host = HostInfo(self.host_id_counter,self.config["password_generator"], default_language=self.config["language"])
                host = host.edit_interactive(project=self)
                if host:
                    self.add_host(host)
            if answer['option'] == 'Import hosts':
                answer = prompt([{'type': 'input','name': 'option','message': 'From which path?', 'default' : os.path.abspath(self.config_path)}])
                if os.path.isdir(answer['option']):
                    host_list = os.listdir(answer['option'])
                    for host in host_list:
                        try:
                            new_host = HostInfo.host_info_from_directory(os.path.join(answer['option'],host))
                            if new_host != None:
                                self.add_host(new_host)
                                print("Imported host: {}".format(host))
                            else:
                                print('ERROR: Cannot import host {}'.format(host))
                        except Exception as e:
                            print(e)
                            print('ERROR: Cannot import host {}'.format(host))
                else:
                    print('Invalid path: ' + answer['option'])
            elif answer['option'] == 'Edit QEMU start ID':
                answer = prompt([{'type': 'input','name': 'hostid','message': 'New Start value for hosts:', 'default' : str(self.host_id_start)}])
                if answer['hostid']:
                    self.change_host_id_start(int(answer['hostid']))
            elif answer['option'] == 'Edit host':
                hosts = list(map(lambda x: x.computer_name, self.hosts))
                answer = prompt([{'type': 'list','name': 'option','message': 'Select a host to edit', 'choices' :hosts}])
                pos = hosts.index(answer['option'])
                self.hosts[pos].edit_interactive(project=self)
                hst = self.hosts[pos]
                if hst.domain != None and ROLE_DOMAIN_CONTROLLER in hst.roles.roles:
                    for dmn in self.domain.domains:
                        if dmn.domain == hst.domain:
                            try:
                                dmn.dc_ip = hst.networks[0].ip_address[0]
                            except:
                                print("Network not configured for DC: {}".format(hst.computer_name))
            elif answer['option'] == 'Delete host':
                hosts = list(map(lambda x: x.computer_name, self.hosts))
                answer = prompt([{'type': 'list','name': 'option','message': 'Select a host to delete', 'choices' : hosts}])
                pos = hosts.index(answer['option'])
                self.hosts.pop(pos)
            elif answer['option'] == 'Back':
                return
            self.scan_hosts()

    def edit_domain_config(self): 
        self.domain.edit_interactive()

    def edit_project_interactive(self):
        self.scan_hosts()
        while True:
            answer = prompt([{'type': 'list','name': 'option','message': 'Select a project property:', 'choices' : ['Description','Edit hosts','AD','SIEM','Config','Build', 'Rebuild','Deploy','Exit'], 'value' : "none"}])
            if answer['option'] == 'Exit':
                self.save()
                return
            elif answer['option'] == 'Edit hosts':
                self.edit_hosts()
            elif answer['option'] == 'SIEM':
                self.edit_siem_config()
            elif answer['option'] == 'Config':
                self.edit_project_config()
            elif answer['option'] == 'Build':
                # Building the project: Creating ISOs, fill templates based on project specifications
                builder = WindowsHostBuilder(self)
                for host in self.hosts:
                    builder.build_host_image(host)
                    # Guardar una vez construido
                    self.save()
                builder.build_net_interfaces()
            elif answer['option'] == 'Rebuild':
                # Rebuilding the project letting the user select the ISOs: Creating ISOs, fill templates based on project specifications
                os.environ['CLEAN_ISOS']='True'
                builder = WindowsHostBuilder(self)
                for host in self.hosts:
                    builder.build_host_image(host)
                builder.build_net_interfaces()
            elif answer['option'] == 'Deploy':
                # Depending if the project is alredy builded it deploys the project in Proxmox etc
                answer = prompt([{'type': 'list','name': 'option','message': 'Deploy mode:', 'choices' : ['Hard','Soft'], 'value' : "none"}])
                # Recreate disk images or only copy the qemu template
                hard_mode = answer['option'] == 'Hard'
                deployer = ProxmoxDeployer(self)
                deployer.create_cpu_if_not_exists("X64")
                deployer.create_cpu_if_not_exists("X86")
                for host in self.hosts:
                    deployer.deploy_host(host,hard_mode)
                # Create resource pool
                deployer.create_pool()
            elif answer['option'] == 'AD':  
                self.edit_domain_config()
            elif answer['option'] == 'Description':  
                answer = prompt([{'type': 'input','name': 'description','message': 'Description of the project', 'default' : self.description}])
                self.description = answer['description']

    def edit_siem_config(self):
        properties = {
            'Sysmon' : self.edit_sysmon,
            'Elasticsearch' : self.edit_elasticsearch, 
            'Logstash' : self.edit_logstash, 
            'Winlogbeat' : self.edit_winlogbeat, 
            'SOCKS Proxy' : self.edit_socks_proxy,
            'Back' : self.save,
        }
        while True:
            answer = prompt([{'type': 'list','name': 'option','message': 'Select a SIEM property:', 'choices' : properties.keys(), 'value' : "none"}])
            if answer['option'] == 'Back':
                self.save()
                return
            elif answer['option'] in properties:
                properties[answer['option']]()
    
    def edit_project_config(self):
        properties = {
            'Password generator' : self.edit_password_generator,
            'Default Admin Password' : self.edit_default_admin_password, 
            'Default Language' : self.edit_default_language, 
            'SSH' : self.edit_ssh, 
            'Network Bridges' : self.network_bridges,
            'Logos' : self.edit_logo,
            'Scripts' : self.edit_scripts,
            'Default scripts' : self.default_scripts,
            'OEM' : self.edit_oem,
            'Back' : self.save,
        }
        while True:
            answer = prompt([{'type': 'list','name': 'option','message': 'Select a Project property:', 'choices' : properties.keys(), 'value' : "none"}])
            if answer['option'] == 'Back':
                self.save()
                return
            elif answer['option'] in properties:
                properties[answer['option']]()
    
    def edit_default_language(self):
        answer = prompt([{'type': 'input','name': 'option','message': 'Default computer language:', 'default' : str(self.config['language'])}])
        self.config['language'] = answer['option']
    
    def edit_oem(self):
        if not 'oem' in self.config:
            self.config['oem'] = {
                'Logo' : None,
                'Manufacturer' : 'CancamusaLabs',
                'Support Phone' : '+00 123456789',
                'Support URL' : 'http://support.com',
                'Support App URL' : 'mailto://support@cancamusa.com',
                'Model' : 'HidenLab',
                'Back' : 'Back'
            }
        while True:
            answer = prompt([{'type': 'list','name': 'option','message': 'Edit logos:', 'choices' : self.config['oem'].keys(), 'value' : "none"}])
            if answer['option'] == 'Back':
                self.save()
                return
            elif answer['option'] == 'Logo':
                if len(self.config['logos']) == 0:
                    print("Load some logos")
                    continue
                logos = list(self.config['logos'])
                selected_logo = prompt([{'type': 'list','name': 'option','message': 'Edit logos:', 'choices' : logos, 'value' : "none"}])
                self.config['oem']['Logo'] = selected_logo['option']
            elif answer['option'] in self.config['oem']:
                value = prompt([{'type': 'input','name': 'option','message': 'Edit property {}:'.format(answer['option']), 'default' : ''}])
                self.config['oem'][answer['option']] = value['option']

    def default_scripts(self):
        if not 'default_scripts' in self.config:
            self.config['default_scripts'] = []
        answer = prompt([{'type': 'checkbox','name': 'option','message': 'Edit scripts:', 'choices': [{'name': x, 'checked': (x in self.config['default_scripts'])} for x in self.config['scripts']]}])
        answer = answer['option']
        for scrpt in self.config['scripts']:
            if scrpt in answer:
                self.config['default_scripts'].append(scrpt)
            else:
                self.config['default_scripts'].remove(scrpt)

    def edit_scripts(self):
        properties = {
            'Add' : self.add_script,
            'Remove' : self.remove_script,
            'Empty' : self.empty_script,
            'Back' : self.save,
        }
        if not 'scripts' in self.config:
            self.config['scripts'] = []
        while True:
            answer = prompt([{'type': 'list','name': 'option','message': 'Edit scripts:', 'choices' : properties.keys(), 'value' : "none"}])
            if answer['option'] == 'Back':
                self.save()
                return
            elif answer['option'] in properties:
                properties[answer['option']]()
    
    def remove_script(self):
        answer = prompt([{'type': 'input','name': 'option','message': 'Script location:', 'default' : ''}])
        self.config['scripts'].remove(answer['option'])  

    def empty_script(self):
        self.config['scripts'] = []
    
    def add_script(self):
        answer = prompt([{'type': 'input','name': 'option','message': 'Script location:', 'default' : ''}])
        script = answer['option']

        script_name = os.path.basename(script)
        
        if not os.path.exists(script):
            print("Path {} does not exist".format(script))
            return
        if script_name in self.config['scripts']:
            return
        
        try:
            with open(script, 'r') as r_f:
                with open(os.path.join('config_files',script_name), 'w') as w_f:
                    w_f.write(r_f.read())
            self.config['scripts'].append(script_name)
        except Exception as e:
            print(e)

    def edit_logo(self):
        properties = {
            'Add' : self.add_logo,
            'Remove' : self.remove_logo,
            'Empty' : self.empty_logo,
            'Back' : self.save,
        }
        if not 'logos' in self.config:
            self.config['logos'] = []
        while True:
            answer = prompt([{'type': 'list','name': 'option','message': 'Edit logos:', 'choices' : properties.keys(), 'value' : "none"}])
            if answer['option'] == 'Back':
                self.save()
                return
            elif answer['option'] in properties:
                properties[answer['option']]()

    def remove_logo(self):
        answer = prompt([{'type': 'input','name': 'option','message': 'Logo location:', 'default' : ''}])
        self.config['logos'].remove(answer['option'])  

    def empty_logo(self):
        self.config['logos'] = []
    
    def add_logo(self):
        answer = prompt([{'type': 'input','name': 'option','message': 'Logo location:', 'default' : ''}])
        logo = answer['option']

        logo_name = os.path.basename(logo)
        
        if not os.path.exists(logo):
            print("Path {} does not exist".format(logo))
            return
        if logo_name in self.config['logos']:
            return
        
        try:
            with open(logo, 'r') as r_f:
                with open(os.path.join('config_files',logo_name), 'w') as w_f:
                    w_f.write(r_f.read())
            self.config['logos'].append(logo_name)
        except Exception as e:
            print(e)
        
    def edit_default_admin_password(self):
        answer = prompt([{'type': 'input','name': 'option','message': 'Default admin password:', 'default' : str(self.config['admin_password'])}])
        self.config['admin_password'] = answer['option']
    
    def edit_password_generator(self):
        answer = prompt([{'type': 'list','name': 'option','message': 'Password generator:','choices' : [cancamusa_common.PASSWORD_GENERATOR_FIRSTNAME_YEAR,cancamusa_common.PASSWORD_GENERATOR_USERNAME_YEAR,cancamusa_common.PASSWORD_GENERATOR_FIRST_LAST_YEAR], 'default' : str(self.config['password_generator'])}])
        self.config['password_generator'] = answer['option']
    
    def network_bridges(self):
        answer = prompt([{'type': 'input','name': 'option','message': 'Start ID of network Bridge:'}])
        self.config['start_vmbr'] = int(answer['option'])


    def edit_ssh(self):
        answer = prompt([{'type': 'confirm','name': 'option','message': 'Enable SSH?:'}])
        enabled = bool(answer['option'])
        self.config['ssh']['enabled'] = enabled
        if not enabled:
            return
        answer = prompt([{'type': 'confirm','name': 'option','message': 'Copy Known Host file?:'}])
        self.config['ssh']['copy_public_key'] = bool(answer['option'])

    def new_project_in_current_path():
        current_dir = os.getcwd()
        return CancamusaProject.new_project_in_path(current_dir)

    def load_from_path(current_dir):
        # Check if the current path is a valid cancamusa project
        cancamusa_config = os.path.join(current_dir, 'cancamusa.json')
        if os.path.isfile(cancamusa_config):
            create_config_path_if_not_exists(current_dir)
            with open(cancamusa_config,'r') as config_file:
                json_config = json.loads(config_file.read())
                cancamusa = CancamusaProject.load_from_object(json_config)
                cancamusa.config_path = current_dir
                return cancamusa
        else:
            raise Exception("Not a valid cancamusa project")

    def load_from_current_path():
        current_dir = os.getcwd()
        return CancamusaProject.load_from_path(current_dir)
        
def create_config_path_if_not_exists(cancamusa_home):
    config_path = os.path.join(cancamusa_home,'config_files')
    try:
        os.makedirs(config_path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

def copy_config_file(cancamusa_home, file_to_copy, new_name):
    config_path = os.path.join(cancamusa_home,'config_files')
    if not os.path.isfile(file_to_copy):
        # TODO: Check if its a http file
        if file_to_copy.startswith("http"):
            r = requests.get(file_to_copy)
            if r.status_code == 200:
                with open(os.path.join(config_path,new_name), 'wb') as f:
                    f.write(r.content)
                return
            else:
                raise Exception('Can\'t download file ' + file_to_copy )
        else:
            raise Exception('File ' + file_to_copy + ' does not exists')
    with open(file_to_copy, 'r') as read_file:
        with open(os.path.join(config_path,new_name), 'w') as write_file:
            write_file.write(read_file.read())
    

def create_custom_winlogbeat_file(cancamusa):
    file_content = "winlogbeat.event_logs:\n"
    file_content += "\t- name: Application\n"
    file_content += "\t\tignore_older: 72h\n"
    file_content += "\t- name: Security\n"
    file_content += "\t- name: System\n"

    if 'sysmon' in cancamusa.config:
        file_content += "\t- name: Microsoft-Windows-Sysmon/Operational\n"
    file_content += "\n\n\n"
    if 'logstash' in cancamusa.config['siem']:
        logstash_conf = cancamusa.config['siem']['logstash']
        file_content += "output.logstash:\n"
        file_content += '\thosts:["{}"]\n'.format(logstash_conf['host'])
    elif 'elasticsearch' in cancamusa.config['siem']:
        elastic_conf = cancamusa.config['siem']['elasticsearch']
        file_content += "output.elasticsearch:\n"
        file_content += '\thosts:["{}"]\n'.format(elastic_conf['host'])
        if 'security' in elastic_conf:
            if 'username' in elastic_conf['security']:
                file_content += '\tusername: "{}"\n'.format(elastic_conf['security']['username'])
                file_content += '\tpassword: "{}"\n'.format(elastic_conf['security']['password'])
            elif 'api_key' in elastic_conf['security']:
                file_content += '\tapi_key: "{}"\n'.format(elastic_conf['security']['api_key'])
            elif 'certificate' in elastic_conf['security']:
                file_content += '\tssl.certificate: "./elastic_certificate.pem"\n'
                file_content += '\tssl.key: "./elastic_key.pem"\n'
    
    return file_content.replace("\n","\r\n")

