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
    if '10' in win_image.lower():
        return 'win10'
    if '7' in win_image.lower():
        return 'win7'
    raise Exception('Cannot identify Windows OS version: ' + win_image)

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
    elif 'Evaluation' in win_image:
        return 'Evaluation'
    elif 'SERVERSTANDARDCORE' in win_image:
        return 'SERVERSTANDARDCORE'
    elif 'SERVERSTANDARD' in win_image:
        return 'SERVERSTANDARD'
    elif 'SERVERDATACENTERCORE' in win_image:
        return 'SERVERDATACENTERCORE'
    elif 'SERVERDATACENTER' in win_image:
        return 'SERVERDATACENTER'
    else:
        return None

def generate_account_name(full_name,alg):
    if alg == ACCOUNT_FORMAT_NAME_DOT_SURNAME:
        return ".".join(full_name.lower().split(" "))
    elif alg == ACCOUNT_FORMAT_TRHEE_LETTERS:
        arr = full_name.lower().split(" ")
        return arr[0][:3] + arr[1][:3]
    elif alg == ACCOUNT_FORMAT_LETTER_SURNAME:
        arr = full_name.lower().split(" ")
        return arr[0][0] + arr[1]
    else:
        return full_name