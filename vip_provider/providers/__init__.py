from vip_provider.providers.base import ProviderBase
from vip_provider.providers.aws import ProviderAWS
from vip_provider.providers.networkapi import ProviderNetworkAPI
from vip_provider.providers.gce import ProviderGce
from vip_provider.providers.ingress import ProviderIngress


def get_provider_to(provider_name):
    for cls in ProviderBase.__subclasses__():
        if cls.get_provider() == provider_name:
            return cls

    raise NotImplementedError("No provider to '{}'".format(provider_name))
