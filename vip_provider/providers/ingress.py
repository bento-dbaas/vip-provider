from vip_provider.providers.base import ProviderBase
from vip_provider.models import Vip


class ProviderIngress(ProviderBase):

    @classmethod
    def get_provider(cls):
        return 'ingress'

    def _create_vip(self, vip):
        vip.save()
        return vip
