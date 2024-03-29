from requests import post
from traceback import print_exc
from vip_provider.models import Vip
from vip_provider.settings import INGRESS_URL
from vip_provider.providers.base import ProviderBase


class ProviderIngress(ProviderBase):

    _ingress_initial_port = 3306

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

    def create_vip(self, group, port, equipments, vip_dns,
                   ingress_provider_team_name=None,
                   ingress_provider_region=None,
                   ingress_provider_db_name=None):
        vip = Vip()
        vip.port = port
        vip.group = group
        vip.equipments = equipments
        vip.vip_dns = vip_dns

        #INGRESS ONLY VARIABLES
        vip.ingress_provider_region = ingress_provider_region
        vip.ingress_provider_team_name = ingress_provider_team_name
        vip.ingress_provider_db_name = ingress_provider_db_name

        self._create_vip(vip)
        return None

    def create_instance_group(self, group, port, equipments, vip):
        if vip:
            vip_obj = Vip.objects(pk=vip).get()
        else:
            vip_obj = Vip.objects(group=group).get()
        vip_obj.port = port
        vip_obj.vip_id = group
        vip_obj.vip_ip = ""

        # INGRESS fields fill
        vip_obj.ingress_provider_hosts_ips = list(map(lambda x: x[u'host_address'], equipments))
        vip_obj.save()
        instance_groups = []
        return vip_obj, instance_groups

    def _create_healthcheck(self, vip):
        '''
        Atualmente retorna apenas o nome do healthcheck. Nao eh criado algo ainda
        pois o ingress nao da suporte para tal
        NOTA: eh necessario implementar o a funcionalidade de CRIAR o healthcheck
        '''
        #TODO implement healthcheck
        hc_name = "hc-%s" % vip.group
        return hc_name

    def _create_backend_service(self, vip):
        '''
        Atualmente retorna apenas o nome do backend_service. Nao eh criado algo ainda
        pois o ingress nao da suporte para tal
        '''
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

    def _prepare_ingress_data(self, vip):
        data = {
            "team": vip.ingress_provider_team_name,
            "bank_port": self._ingress_initial_port,
            "bank_address": vip.ingress_provider_hosts_ips,
            "bank_type": 'MySQLFOXHA',
            "bank_name": vip.ingress_provider_db_name,
            "region": vip.ingress_provider_region
        }
        return data

    def _allocate_ip(self, vip):
        ip_name = "%s-lbip" % vip.group

        """
        NAO HA NECESSIDADE DE CRIAR NOVO VIP COM INGRESSLB,
         basta usar mesmas infos ja fornecidas pelo Ingress Provider 
        """
        if vip.vip_ip != '':
            return {'name': ip_name, 'address': vip.vip_ip, 'port': vip.port}

        data = self._prepare_ingress_data(vip)
        ingress_url = "{}/ingresslb/".format(INGRESS_URL)
        try:
            response = self._request(post, ingress_url, json=data, timeout=360000)
            if response.status_code != 201:
                #TODO informar motivo da request nao ser 201
                raise response.raise_for_status()
            ingress_prov_response = response.json()['value']
        except Exception:
            print_exc()
            raise Exception
        vip.port = ingress_prov_response.get('port_external')
        addresses = ingress_prov_response.get('ip_external')
        return {'name': ip_name, 'address': addresses, 'port': vip.port}

    def destroy_allocate_ip(self, vip):
        vip_obj = Vip.objects(pk=vip).get()
        self._destroy_allocate_ip(vip_obj)

        vip_obj.vip_ip = ""
        vip_obj.vip_ip_name = None
        vip_obj.save()
        return True

    def _destroy_allocate_ip(self, vip):
        #TODO implementar remocao de LB no ingress provider
        pass
