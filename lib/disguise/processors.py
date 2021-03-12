PROCESSORS = [
    {'processor': "athlon",'family':'AMD'},
    {'processor': "EPYC",'family':'AMD'},
    {'processor': "EPYC-IBPB",'family':'AMD'},
    {'processor': "EPYC-Rome",'family':'AMD'},
    {'processor': "Opteron_G1",'family':'AMD'},
    {'processor': "Opteron_G2",'family':'AMD'},
    {'processor': "Opteron_G3",'family':'AMD'},
    {'processor': "Opteron_G4",'family':'AMD'},
    {'processor': "Opteron_G5",'family':'AMD'},
    {'processor': "phenom",'family':'AMD'},
    {'processor': "486",'family':'Intel'},
    {'processor': "Broadwell",'family':'Intel'},
    {'processor': "Broadwell-IBRS",'family':'Intel'},
    {'processor': "Broadwell-noTSX",'family':'Intel'},
    {'processor': "Broadwell-noTSX-IBRS",'family':'Intel'},
    {'processor': "Cascadelake-Server",'family':'Intel'},
    {'processor': "Cascadelake-Server-noTSX",'family':'Intel'},
    {'processor': "Conroe",'family':'Intel'},
    {'processor': "core2duo",'family':'Intel'},
    {'processor': "coreduo",'family':'Intel'},
    {'processor': "Haswell",'family':'Intel'},
    {'processor': "Haswell-IBRS",'family':'Intel'},
    {'processor': "Haswell-noTSX",'family':'Intel'},
    {'processor': "Haswell-noTSX-IBRS",'family':'Intel'},
    {'processor': "Icelake-Client",'family':'Intel'},
    {'processor': "Icelake-Client-noTSX",'family':'Intel'},
    {'processor': "Icelake-Server",'family':'Intel'},
    {'processor': "Icelake-Server-noTSX",'family':'Intel'},
    {'processor': "IvyBridge",'family':'Intel'},
    {'processor': "IvyBridge-IBRS",'family':'Intel'},
    {'processor': "KnightsMill",'family':'Intel'},
    {'processor': "Nehalem",'family':'Intel'},
    {'processor': "Nehalem-IBRS",'family':'Intel'},
    {'processor': "Penryn",'family':'Intel'},
    {'processor': "pentium",'family':'Intel'},
    {'processor': "pentium2",'family':'Intel'},
    {'processor': "pentium3",'family':'Intel'},
    {'processor': "SandyBridge",'family':'Intel'},
    {'processor': "SandyBridge-IBRS",'family':'Intel'},
    {'processor': "Skylake-Client",'family':'Intel'},
    {'processor': "Skylake-Client-IBRS",'family':'Intel'},
    {'processor': "Skylake-Client-noTSX-IBRS",'family':'Intel'},
    {'processor': "Skylake-Server",'family':'Intel'},
    {'processor': "Skylake-Server-IBRS",'family':'Intel'},
    {'processor': "Skylake-Server-noTSX-IBRS",'family':'Intel'},
    {'processor': "Westmere",'family':'Intel'},
    {'processor': "Westmere-IBRS",'family':'Intel'},
    {'processor': "kvm32",'family':'QEMU'},
    {'processor': "kvm64",'family':'QEMU'},
    {'processor': "max",'family':'QEMU'},
    {'processor': "qemu32",'family':'QEMU'},
    {'processor': "qemu64",'family':'QEMU'},
    {'processor': "host",'family':'Host'}
]

def list_processors(family=None): 
    to_ret = []
    for el in PROCESSORS:
        if family and el['family'] == family:
            to_ret.append(el["processor"])
            continue
        to_ret.append(el["processor"])
    return to_ret