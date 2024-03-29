from vip_provider.providers.base import ProviderBase
from vip_provider.tests.test_credentials import CredentialAddFake


class FakeProvider(ProviderBase):

    @classmethod
    def get_provider(cls):
        return "ProviderForTests"

    def build_client(self):
        return "FakeClient"

    def build_credential(self):
        return "FakeCredential"

    def get_credential_add(self):
        return CredentialAddFake
