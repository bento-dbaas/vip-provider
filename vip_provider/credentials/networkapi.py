from vip_provider.credentials.base import CredentialBase, CredentialAdd

class CredentialNetworkAPI(CredentialBase):

    @property
    def user(self):
        return self.content['user']

    @property
    def password(self):
        return self.content['password']

    @property
    def endpoint(self):
        return self.content['endpoint']

    @property
    def business(self):
        return self.content['business']

    @property
    def cache_group(self):
        return self.content['cache_group']

    @property
    def destination(self):
        return self.content['destination']

    @property
    def env_pool_id(self):
        return self.content['env_pool_id']

    @property
    def env_vip_id(self):
        return self.content['env_vip_id']

    @property
    def finality(self):
        return self.content['finality']

    @property
    def healthcheck_expect(self):
        return self.content['healthcheck_expect']

    @property
    def healthcheck_request(self):
        return self.content['healthcheck_request']

    @property
    def healthcheck_type(self):
        return self.content['healthcheck_type']

    @property
    def id_equipment_type(self):
        return self.content['id_equipment_type']

    @property
    def id_group(self):
        return self.content['id_group']

    @property
    def id_model(self):
        return self.content['id_model']

    @property
    def l4_protocol(self):
        return self.content['l4_protocol']

    @property
    def l7_protocol(self):
        return self.content['l7_protocol']

    @property
    def l7_rule(self):
        return self.content['l7_rule']

    @property
    def lb_method(self):
        return self.content['lb_method']

    @property
    def limit(self):
        return self.content['limit']

    @property
    def member_status(self):
        return self.content['member_status']

    @property
    def persistence(self):
        return self.content['persistence']

    @property
    def priority(self):
        return self.content['priority']

    @property
    def servicedownaction(self):
        return self.content['servicedownaction']

    @property
    def timeout(self):
        return self.content['timeout']

    @property
    def traffic_return(self):
        return self.content['traffic_return']

    @property
    def vm_name(self):
        return self.content['vm_name']

    @property
    def weight(self):
        return self.content['weight']


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
