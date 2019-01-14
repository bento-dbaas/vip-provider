from vip_provider.credentials.base import CredentialBase, CredentialAdd

class CredentialNetworkAPI(CredentialBase):
    pass


class CredentialAddNetworkAPI(CredentialAdd):
    def valid_fields(self):
        return [
            'user', 'password', 'endpoint', 'business', 'cache_group',
            'destination', 'env_pool_id', 'env_vip_id', 'finality',
            'healthcheck_expect', 'healthcheck_request', 'healthcheck_type',
            'id_equipment_type', 'id_group', 'id_model', 'l4_protocol',
            'l7_protocol', 'l7_rule', 'lb_method', 'limit', 'member_status',
            'persistence', 'priority', 'servicedownaction', 'timeout',
            'traffic_return', 'vm_name', 'weight'
        ]
