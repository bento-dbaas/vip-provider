from vip_provider.providers.base import ProviderBase
from requests import post, get, delete
from vip_provider.models import Vip
from vip_provider.settings import INGRESS_URL


class ProviderIngress(ProviderBase):

    @classmethod
    def get_provider(cls):
        return 'ingress'

    def _request(self, action, url, **kw):
        return action(url, verify=False, **kw)

    def _create_vip(self, vip):
        vip.vip_id = vip.group
        vip.vip_ip = ''
        vip.save()
        return None

    def create_instance_group(self, group, port, equipments, vip):
        if vip:
            vip_obj = Vip.objects(pk=vip).get()
        else:
            vip_obj = Vip()
        vip_obj.port = port
        vip_obj.group = group
        vip_obj.vip_id = group
        vip_obj.vip_ip = ""

        # INGRESS fields fill
        vip_obj.hosts_ips = list(map(lambda x: x[u'host_address'], equipments))
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

    def _get_create_ingress_data(self, vip):
        data = {
            "team": vip.team_name,
            "bank_port": vip.port,
            "bank_address": vip.hosts_ips,
            "bank_type": 'MySQLFOXHA',
            "bank_name": vip.group,
            "region": vip.region
        }
        return data

    def _allocate_ip(self, vip):
        ip_name = "%s-lbip" % vip.group
        data = self._get_create_ingress_data(vip)
        ingress_url = "{}/ingresslb/".format(INGRESS_URL)
        try:
            response = self._request(post, ingress_url, json=data, timeout=6000)
            if response.status_code not in [200, 201]:
                raise response.raise_for_status()
            ingress = response.json()['value']
        except Exception as error:
            print(error)
            raise Exception
        vip.port = ingress.get('port_external')
        addresses = ingress.get('ip_external')
        return {'name': ip_name, 'address': addresses}

    def destroy_allocate_ip(self, vip):
        vip_obj = Vip.objects(pk=vip).get()
        self._destroy_allocate_ip(vip_obj)

        vip_obj.vip_ip = ""
        vip_obj.vip_ip_name = None
        vip_obj.save()
        return True

    def _destroy_allocate_ip(self, vip):
        pass
