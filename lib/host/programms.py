
class HostInfoPrograms:
    def __init__(self, display_name, display_version, publisher, install_date):
        self.display_name = display_name
        self.display_version = display_version
        self.publisher = publisher
        self.install_date = install_date

    def edit_interactive(self):
        # Don't know what to do here
        return self

    def to_json(self):
        return {
            'DisplayName': self.display_name,
            'DisplayVersion': self.display_version,
            'Publisher': self.publisher,
            'InstallDate': self.install_date
        }

    def from_json(obj):
        return HostInfoPrograms(obj['DisplayName'], obj['DisplayVersion'], obj['Publisher'], obj['InstallDate'])