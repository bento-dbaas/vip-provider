from vip_provider.credentials.base import CredentialAdd, CredentialBase


class CredentialGce(CredentialBase):
    @property
    def project(self):
        return self.content['project']


    @property
    def scopes(self):
        return self.content['scopes']

    @property
    def region(self):
        return self.content['region']

    @property
    def subnetwork(self):
        return self.content['subnetwork']


class CredentialAddGce(CredentialAdd):

    @classmethod
    def is_valid(cls, content):
        return True, ""
