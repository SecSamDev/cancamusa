# Install KMS server

Clone KMS repository: https://github.com/SystemRage/py-kms.git
Install Python3.9: `apt install python3.9 --fix-missing`

Install as service:
```
[Unit]
Description=KMS server
After=network.target auditd.service

[Service]
WorkingDirectory=/root/py-kms/py-kms
ExecStart=/usr/bin/python3.9 /root/py-kms/py-kms/pykms_Server.py 0.0.0.0 1688 -V DEBU
G -F /var/log/pykms_logserver.log -s /root/pykms.db -c 30
KillMode=process
Restart=on-failure
RestartPreventExitStatus=255

[Install]
WantedBy=multi-user.target
```