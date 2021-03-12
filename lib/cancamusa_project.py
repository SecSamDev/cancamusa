import os
import json
from PyInquirer import prompt
import cancamusa_common
import errno
import requests
from cancamusa_host import HostInfo
from host_builder import WindowsHostBuilder
from cancamusa_domain import CancamusaDomain

class CancamusaProject:
    """ Loads and stores information about a Cancamusa project """
    def __init__(self, config_path):
        self.project_name = "Cancamusa"
        self.description = "A simple lab project"
        self.config_path = config_path
        self.virtio = 'stable'
        self.domain = CancamusaDomain()
        self.config = {
            'siem' : {},
            'account_generator' : cancamusa_common.ACCOUNT_FORMAT_NAME_DOT_SURNAME
        }
        self.hosts = []
    

    def add_host(self,host):
        # Do validation/transformation
        self.hosts.append(host)
        return self

    def save(self):
        if not self.config_path:
            raise Exception("Invalid config file path")
        with open(os.path.join(self.config_path,'cancamusa.json'), 'w') as config_file:
            to_write = {
                'project_name' : self.project_name,
                'description' : self.description,
                'config' : self.config,
                'virtio' : self.virtio,
                'hosts' : [],
                'domain' : self.domain.to_json()
            }
            for host in self.hosts:
                to_write['hosts'].append(host.to_json())
            config_file.write(json.dumps(to_write,indent=4,))
        return self

    def load_from_object(obj):
        cancamusa = CancamusaProject(None)
        cancamusa.project_name = obj['project_name']
        cancamusa.description = obj['description']
        cancamusa.virtio = obj['virtio']
        cancamusa.config = obj['config']
        cancamusa.hosts = []
        cancamusa.domain = CancamusaDomain.load_from_object(obj['domain'])
        for host in obj['hosts']:
            cancamusa.add_host(HostInfo.from_json(host))
        return cancamusa

    def set_elasticsearch_siem(self, host, security):
        self.config['siem']['elasticsearch'] = {
            'host' : host
        }
        if security:
            self.config['siem']['elasticsearch']['security'] = security
        return self

    def set_sysmon_conf(self, conf_path):
        self.config['sysmon'] = {
            'conf' : conf_path
        }
        return self
    
    def set_winlogbeat_conf(self, conf_path):
        self.config['winlogbeat'] = {
            'conf' : conf_path
        }
        return self

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
        answers = prompt([{'type': 'input','name': 'winlogbeat','message': 'WinLogBeat configuration file path'}])
        if answers['winlogbeat'].strip() == "":
            print("Creating custom winlogbeat configuration file...")
            content = create_custom_winlogbeat_file(self)
            with open(os.path.join(self.config_path,'config_files',cancamusa_common.WINLOGBEAT_CONFIG_FILE), 'w') as write_file:
                write_file.write(content)
        else:
            copy_config_file(self.config_path,answers['winlogbeat'],cancamusa_common.WINLOGBEAT_CONFIG_FILE)
            self.set_winlogbeat_conf(answers['winlogbeat'])

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
    

    def edit_sysmon(self):
        answers = prompt([{'type': 'confirm','name': 'sysmon','message': 'Install Sysmon in each host?'}])
        if answers['sysmon']:
            answers = prompt([{'type': 'input','name': 'sysmon_conf','message': 'Sysmon configuration file path'}])
            self.set_sysmon_conf(answers['sysmon_conf'])
            copy_config_file(self.config_path,answers['sysmon_conf'],cancamusa_common.SYSMON_CONFIG_FILE)

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
            options =  ['Add host','Import hosts']
            if len(self.hosts) > 0:
                options.append('Show hosts')
                options.append('Edit host')
                options.append('Delete host')
            options.append('Back')
            answer = prompt([{'type': 'list','name': 'option','message': 'Host edition mode', 'choices' : options}])
            if answer['option'] == 'Show hosts':
                for host in self.hosts:
                    print(host)

            if answer['option'] == 'Add host':
                host = HostInfo()
                host = host.edit_interactive()
                if host:
                    self.add_host(host)
            if answer['option'] == 'Import hosts':
                answer = prompt([{'type': 'input','name': 'option','message': 'From which path?', 'default' : os.path.abspath(self.config_path)}])
                if os.path.isdir(answer['option']):
                    host_list = os.listdir(answer['option'])
                    for host in host_list:
                        #try:
                        new_host = HostInfo.host_info_from_directory(os.path.join(answer['option'],host))
                        if new_host != None:
                            self.add_host(new_host)
                            print("Imported host: {}".format(host))
                        else:
                            print('ERROR: Cannot import host {}'.format(host))
                        #except Exception as e:
                        #    print(e)
                        #    print('ERROR: Cannot import host {}'.format(host))
                else:
                    print('Invalid path: ' + answer['option'])
            elif answer['option'] == 'Edit host':
                hosts = list(map(lambda x: x.computer_name, self.hosts))
                answer = prompt([{'type': 'list','name': 'option','message': 'Select a host to edit', 'choices' :hosts}])
                pos = hosts.index(answer['option'])
                self.hosts[pos].edit_interactive()
            elif answer['option'] == 'Delete host':
                hosts = list(map(lambda x: x.computer_name, self.hosts))
                answer = prompt([{'type': 'list','name': 'option','message': 'Select a host to delete', 'choices' : hosts}])
                pos = hosts.index(answer['option'])
                self.hosts.pop(pos)
            elif answer['option'] == 'Back':
                return

    def edit_domain_config(self): 
        self.domain.edit_interactive()

    def edit_project_interactive(self):
        while True:
            answer = prompt([{'type': 'list','name': 'option','message': 'Select a project property:', 'choices' : ['Description','Edit hosts','AD','Build','Deploy','Exit'], 'value' : "none"}])
            if answer['option'] == 'Exit':
                self.save()
                return
            elif answer['option'] == 'Edit hosts':
                self.edit_hosts()
            elif answer['option'] == 'SIEM':
                self.edit_siem_config()
            elif answer['option'] == 'Build':
                # Building the project: Creating ISOs, fill templates based on project specifications
                builder = WindowsHostBuilder(self)
                for host in self.hosts:
                    builder.build_host_image(host)
            elif answer['option'] == 'Deploy':
                # Depending if the project is alredy builded it deploys the project in Proxmox etc
                pass
            elif answer['option'] == 'AD':  
                self.edit_domain_config()
            elif answer['option'] == 'Description':  
                answer = prompt([{'type': 'input','name': 'description','message': 'Description of the project', 'default' : self.description}])
                self.description = answer['description']

    def edit_siem_config(self):
        while True:
            answer = prompt([{'type': 'list','name': 'option','message': 'Select a SIEM property:', 'choices' : ['Sysmon', 'Elasticsearch','Logstash','Winlogbeat','Back'], 'value' : "none"}])
            if answer['option'] == 'Back':
                self.save()
                return
            elif answer['option'] == 'Sysmon':
                self.edit_sysmon() 
            elif answer['option'] == 'Elasticsearch':
                self.edit_elasticsearch() 
            elif answer['option'] == 'Logstash':
                self.edit_logstash() 
            elif answer['option'] == 'Winlogbeat':  
                self.edit_winlogbeat()

    def new_project_in_current_path():
        current_dir = os.getcwd()
        return CancamusaProject.new_project_in_path(current_dir)

    def load_from_path(current_dir):
        # Check if the current path is a valid cancamusa project
        cancamusa_config = os.path.join(current_dir, 'cancamusa.json')
        if os.path.isfile(cancamusa_config):
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
    
    return file_content

