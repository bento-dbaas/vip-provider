from vip_provider.providers.base import ProviderBase
from vip_provider.models import Vip


class ProviderIngress(ProviderBase):

    @classmethod
    def get_provider(cls):
        return 'ingress'

    def _create_vip(self, vip):
        vip.save()
        return vip

    def create_instance_group(self, group, port, equipments, vip):
        if vip:
            vip_obj = Vip.objects(pk=vip).get()
        else:
            vip_obj = Vip()
        vip_obj.port = port
        vip_obj.group = group
        vip_obj.vip_ip = ""
        vip_obj.save()

    def _create_healthcheck(self, vip):
        hc_name = "hc-%s" % vip.group
        # Sera inserida a logica de HC do Ingress Provider
        return hc_name

    def _create_backend_service(self, vip):
        bs_name = "bs-%s" % vip.group
        return bs_name

    def allocate_ip(self, vip):
        vip_obj = Vip.objects(pk=vip).get()
        ip_info = self._allocate_ip(vip_obj)

        if ip_info is None:
            return None

        vip_obj.vip_ip_name = ip_info.get('name')
        vip_obj.vip_ip = ip_info.get('address')
        vip_obj.save()
        return ip_info

    def _allocate_ip(self, vip):

        pass

    def destroy_allocate_ip(self, vip):
        vip_obj = Vip.objects(pk=vip).get()
        self._destroy_allocate_ip(vip_obj)

        vip_obj.vip_ip = ""
        vip_obj.vip_ip_name = None
        vip_obj.save()
        return True

    def _destroy_allocate_ip(self, vip):
        pass
