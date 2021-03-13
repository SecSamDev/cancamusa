import uuid

SYSMON_CONFIG_FILE = 'sysmon-config.xml'
WINLOGBEAT_CONFIG_FILE = 'winlogbeat.yml'
ELASTIC_CERTIFICATE = 'elastic_certificate.pem'
ELASTIC_CERTIFICATE_KEY = 'elastic_certificate.key'

# For random account generation
ACCOUNT_FORMAT_EXAMPLE = "Bill Doe Ferguson"
ACCOUNT_FORMAT_NAME_DOT_SURNAME = "bill.doe"
ACCOUNT_FORMAT_LETTER_SURNAME = "bdoe"
ACCOUNT_FORMAT_TRHEE_LETTERS = "bildoefer"

def random_guid():
    return str(uuid.uuid4())

def translate_lang(lang):
    if lang.lower() == "en":
        return "en-EN"
    if lang.lower() == "es":
        return "es-ES"
    return "en-EN"

def get_win_type(win_image):
    if '2008' in win_image:
        return 'win2008'
    if '2016' in win_image:
        return 'win2016'
    if '2019' in win_image:
        return 'win2019'
    if 'windows 10' in win_image.lower():
        return 'win10'
    if 'windows 7' in win_image.lower():
        return 'win7'
    raise Exception('Cannot identify Windows OS version: ' + win_image)

def replaceArgumentsFunction(content, arguments):
    return content.replace('__LANG__', translate_lang(arguments.lang)).replace('__LANG_FALL__', translate_lang(arguments.lang_fall)).replace('__USR_NAME__', arguments.username).replace('__VERSION__', arguments.version).replace('__KVM__', arguments.kvm).replace('__USR_PSWD__', arguments.password).replace('__VIRTIO__', arguments.virtio).replace('__WIN_IMG__', str(arguments.win_image)).replace('__MACHINE_NAME__', arguments.machine_name).replace('__ISO_PATH__', arguments.iso_path).replace('__IMG_SELECTOR__', arguments.win_image_type).replace('__ISO_CHECKSUM__', arguments.iso_md5).replace('__VIRTIO_PATH__',arguments.virtio_path).replace('__CORP_COMMAND__', ' '.join(sys.argv).replace('\\','/'))

def get_win_image_type(win_image):
    win_image = win_image.lower()
    if 'enterprise' in win_image:
        return 'Enterprise'
    elif 'home' in win_image:
        return 'Home'
    elif 'Pro' in win_image:
        return 'Professional'
    elif 'Edu' in win_image:
        return 'Educational'
    else:
        return 'Pro'