# -*- coding: utf-8 -*-
from vip_provider.providers.base import ProviderBase
from vip_provider.credentials.networkapi import CredentialNetworkAPI
from vip_provider.credentials.networkapi import CredentialAddNetworkAPI
from networkapiclient.ClientFactory import ClientFactory
from networkapiclient.exception import NetworkAPIClientError
from vip_provider.models import Vip

#from networkapiclient.ClientFactory import ClientFactory
#from networkapiclient.exception import NetworkAPIClientError


class ProviderNetworkAPI(ProviderBase):

    def __init__(self, environment):
        super(ProviderNetworkAPI, self).__init__(environment)
        self.equipment_api = self.client.create_equipamento()
        self.environment_api = self.client.create_ambiente()
        self.ip_api = self.client.create_ip()
        self.vip_api = self.client.create_api_environment_vip()
        self.vip_api_request = self.client.create_api_vip_request()
        self.pool_api = self.client.create_pool()
        self.pool_deploy = self.client.create_api_pool_deploy()

    @classmethod
    def get_provider(cls):
        return 'networkapi'

    def get_create_pull_data(self, vip):

        new_pool = {
            "environment": int(self.credential.env_pool_id),
            "lb_method": self.credential.lb_method,
            "server_pool_members": [],
            "servicedownaction": {"name": self.credential.servicedownaction},
            "default_port": vip.port,
            "healthcheck": {
                "healthcheck_type": self.credential.healthcheck_type,
                "destination": self.credential.destination,
                "healthcheck_expect": self.credential.healthcheck_expect,
                "identifier": "",
                "healthcheck_request": self.credential.healthcheck_request.format(vip.group)
            },
            "default_limit": int(self.credential.limit),
            "identifier": 'DBaaS_{}'.format(vip.group)
        }

        for equipment_dict in vip.equipments:
            equipment = Equipment(
                name='{}-{}'.format(
                    self.credential.vm_name, equipment_dict['identifier']),
                ip=equipment_dict['host_address'],
                port=int(equipment_dict['port'])
            )
            equipment.id = self._get_equipment_id(equipment.name)
            equipment.environment_id = self._get_equipment_environment_id(
                equipment.id)
            equipment.ip_id = self._get_ip_id(
                equipment.ip, equipment.environment_id
            )
            new_pool['server_pool_members'].append({
                "priority": int(self.credential.priority),
                "port_real": equipment.port,
                "identifier": equipment.name,
                "limit": int(self.credential.limit),
                "member_status": int(self.credential.member_status),
                "weight": int(self.credential.weight),
                "equipment": {
                    "id": int(equipment.id),
                    "nome": equipment.name
                },
                "ip": {
                    "ip_formated": equipment.ip,
                    "id": int(equipment.ip_id)
                },
                "ipv6": None,
                "id": None
            })

        return new_pool

    def get_create_vip_data(self, vip, pool_id):
        new_vip = {
            "business": self.credential.business,
            "environmentvip": int(self.credential.env_vip_id),
            "ipv4": self._get_ipv4_for_vip(
                int(self.credential.env_vip_id), vip.vip_dns),
            "ipv6": None,
            "name": vip.vip_dns,
            "options": {
                "cache_group": int(self.credential.cache_group),
                "persistence": int(self.credential.persistence),
                "timeout": int(self.credential.timeout),
                "traffic_return": int(self.credential.traffic_return),
            },
            "ports": [{
                "options": {
                    "l4_protocol": int(self.credential.l4_protocol),
                    "l7_protocol": int(self.credential.l7_protocol),
                },
                "pools": [{
                    "l7_rule": int(self.credential.l7_rule),
                    "l7_value": '',
                    "server_pool": pool_id
                }],
                "port": vip.port
            }],
            "service": vip.vip_dns.split('.')[0]
        }

        return new_vip

    def _create_vip(self, vip):
        new_pool = self.get_create_pull_data(vip)
        pool = self.pool_api.save_pool(new_pool)
        pool_id = pool[0]['id']

        try:
            new_vip = self.get_create_vip_data(vip, pool_id)
            vip_db = self.vip_api_request.save_vip_request(new_vip)
            vip_id = vip_db[0]['id']
        except NetworkAPIClientError as e:
            self.delete_pool(pool_id)
            raise NetworkAPIClientError(str(e))
        except Exception as e:
            self.delete_pool(pool_id)
            raise Exception('Unexpected error on save_vip_request... ' + str(e))

        try:
            net_vip = self.vip_api_request.create_vip(vip_id)
        except NetworkAPIClientError as e:
            self.delete_vip_request(vip_id)
            self.delete_pool(pool_id)
            raise NetworkAPIClientError(str(e))
        except Exception as e:
            self.delete_vip_request(vip_id)
            self.delete_pool(pool_id)
            raise Exception('Unexpected error on save_vip_request... ' + str(e))

        vip.vip_id = str(vip_id)
        vip.pool_id = str(pool_id)
        vip.vip_ip = self.get_vip_ip(vip_id)
        vip.dscp = self.get_dscp(vip_id)

    def _update_vip_reals(self, vip_reals, identifier):
        vip = Vip.objects(id=identifier).get()
        vip.equipments = vip_reals
        pool_data = self.get_create_pull_data(vip=vip)
        pool = self.pool_api.get_pool(vip.pool_id)['server_pools'][0]
        pool['server_pool_members'] = pool_data['server_pool_members']
        self.pool_deploy.update([pool])
        return vip

    def build_credential(self):
        return CredentialNetworkAPI(self.provider, self.environment)

    def get_credential_add(self):
        return CredentialAddNetworkAPI

    def build_client(self):
        client = ClientFactory(
            networkapi_url=self.credential.endpoint,
            user=self.credential.user, password=self.credential.password
        )
        return client

    def _get_equipment_id(self, name):
        equipment = self.equipment_api.listar_por_nome(nome=name)
        return equipment['equipamento']['id']

    def _get_equipment_environment_id(self, equip_id):
        environment = self.environment_api.listar_por_equip(equip_id=equip_id)
        return environment['ambiente']['id']

    def _get_ip_id(self, ip, environment):
        ip = self.ip_api.buscar_por_ip_ambiente(
            ip=ip,id_environment=environment)
        return ip['ip']['id']

    def _get_ipv4_for_vip(self, vip_env_id, name):
        ipv4 = self.ip_api.get_available_ip4_for_vip(vip_env_id, name)
        return int(ipv4['ip']['id'])

    def delete_pool(self, pool_id):
        output = self.pool_api.delete_pool(pool_id)

    def delete_vip_request(self, vip_id):
        output = self.vip_api_request.delete_vip_request(vip_id)

    def _delete_vip(self, vip_obj):
        self.vip_api_request.remove_vip(vip_obj.vip_id)
        self.delete_vip_request(vip_obj.vip_id)

    def get_dscp(self, vip_id):
        data = self.vip_api_request.get_vip_request_details(vip_id)
        return data['vips'][0]['dscp']

    def get_vip_ip(self, vip_id):
        data = self.vip_api_request.get_vip_request_details(vip_id)
        return data['vips'][0]['ipv4']['ip_formated']


class Equipment(object):
    def __init__(self, name, ip, port):
        self.name = name
        self.ip = ip
        self.port = port
