from collections import namedtuple
from time import sleep
from traceback import print_exc
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from vip_provider.settings import AWS_PROXY
from vip_provider.credentials.aws import CredentialAWS, CredentialAddAWS
from vip_provider.providers.base import ProviderBase
from vip_provider.clients.team import TeamClient
from vip_provider.drivers.aws import NetworkLBDriver
from dns.resolver import Resolver
from dns.exception import DNSException


STATE_AVAILABLE = 'active'
STATE_INUSE = 'inuse'
ATTEMPTS = 60
DELAY = 5
SimpleEbs = namedtuple('ebs', 'id')


class ProviderAWS(ProviderBase):

    @classmethod
    def get_provider(cls):
        return 'ec2'

    def build_client(self):
        client = NetworkLBDriver(
            self.credential.access_id,
            self.credential.secret_key,
            region=self.credential.region,
            **{'proxy_url': AWS_PROXY} if AWS_PROXY else {}
        )

        if AWS_PROXY:
            client.connection.connection.session.proxies.update({
                'https': AWS_PROXY.replace('http://', 'https://')
            })
        return client

    def build_credential(self):
        return CredentialAWS(self.provider, self.environment)

    def get_credential_add(self):
        return CredentialAddAWS

    def __waiting_be(self, state, vip_obj):
        vip = self.client.get_balancer(vip_obj.id)
        for _ in range(ATTEMPTS):
            if vip.state == state:
                return True
            sleep(DELAY)
            vip = self.client.get_balancer(vip_obj.id)
        raise EnvironmentError("Vip {} is {} should be {}".format(
            vip_obj.id, vip.state, state
        ))

    def waiting_be_available(self, vip):
        return self.__waiting_be(STATE_AVAILABLE, vip)

    @staticmethod
    def dns2ip(dns, retries=90, wait=1):
        resolver = Resolver()
        for attempt in range(0, retries):

            try:
                answer = resolver.query(dns)
            except DNSException:
                pass
            else:
                ips = [str(a) for a in answer]
                if ips:
                    return ips[0]

            sleep(wait)

        return False

    def register_targets(self, balancer_id, target_group_id, zone_id, instances):
        self.client.register_targets(target_group_id, instances)

    def get_vip_healthy(self, vip):
        return self.client.get_target_healthy(vip.target_group_id)

    def _create_vip(self, vip):
        new_balancer = self.client.create_balancer(
            name=vip.group,
            port=vip.port,
            subnets=list(self.credential.zones.keys())
        )
        self.waiting_be_available(new_balancer)

        healthcheck_config = {
            'HealthCheckIntervalSeconds': 10,
            'HealthCheckPath': '/health-check/foxha/',
            'HealthCheckPort': 80,
            'HealthCheckProtocol': 'HTTP',
            'HealthCheckTimeoutSeconds': 6
        }
        new_target_group = self.client.create_target_group(
            name='tg-{}'.format(vip.group),
            port=vip.port,
            protocol='TCP',
            vpc_id=self.credential.vpc_id,
            healthcheck_config=healthcheck_config,
            healthy_threshold_count=2,
            unhealthy_threshold_count=2,
            target_type='instance'
        )

        self.client.create_listener(
            new_balancer,
            new_target_group,
            protocol='TCP',
            port=3306
        )
        vip.vip_id = new_balancer.id
        vip.vip_ip = self.dns2ip(new_balancer.ip)
        vip.target_group_id = new_target_group.id

    def _delete_vip(self, vip_obj):
        balancer = self.client.get_balancer(vip_obj.vip_id)
        target_group = self.client.get_target_group(balancer_id=balancer.id)
        self.client.destroy_balancer(balancer)
        self.client.destroy_target_group(target_group)
