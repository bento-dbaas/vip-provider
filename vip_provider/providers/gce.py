from vip_provider.providers.base import ProviderBase
from vip_provider.credentials.gce import CredentialGce, CredentialAddGce
from googleapiclient.errors import HttpError

from vip_provider.settings import HTTP_PROXY
import googleapiclient.discovery
from google.oauth2 import service_account

from vip_provider.models import InstanceGroup
import json


class ProviderGce(ProviderBase):

    @classmethod
    def get_provider(cls):
        return 'gce'

    def build_client(self):
        service_account_data = self.credential.content['service_account']
        service_account_data['private_key'] = service_account_data[
            'private_key'
        ].replace('\\n', '\n')

        credentials = service_account.Credentials.from_service_account_info(
            service_account_data,
            scopes=self.credential.scopes
        )

        if HTTP_PROXY:
            _, host, port = HTTP_PROXY.split(':')
            try:
                port = int(port)
            except ValueError:
                raise EnvironmentError('HTTP_PROXY incorrect format')

            proxied_http = httplib2.Http(proxy_info=httplib2.ProxyInfo(
                httplib2.socks.PROXY_TYPE_HTTP,
                host.replace('//', ''),
                port
            ))

            authorized_http = google_auth_httplib2.AuthorizedHttp(
                                credentials,
                                http=proxied_http)

            service = googleapiclient.discovery.build(
                        'compute',
                        'v1',
                        http=authorized_http)
        else:
            service = googleapiclient.discovery.build(
                'compute',
                'v1',
                credentials=credentials,
            )

        return service

    def build_credential(self):
        return CredentialGce(
            self.provider, self.environment
        )

    def __get_instance_group_name(self, group, zone):
        return "%s-%s" % (
            group,
            zone
        )

    def _remove_instance_group(self, instance_group, vip, destroy_vip):
        for ig in instance_group:
            ig_del = self.client.instanceGroups().delete(
                project=self.credential.project,
                zone=ig.zone,
                instanceGroup=ig.name
            ).execute()

            self.wait_operation(
                zone=ig.zone,
                operation=ig_del.get('name')
            )
            ig.delete()

        return True

    def _create_instance_group(self, vip, equipments):
        '''create one group to each zone'''
        groups = []
        for eq in equipments:
            zone = eq.get("zone", None)
            eq_id = eq.get("identifier", None)
            group_name = self.__get_instance_group_name(
                vip.group,
                zone
            )
            if group_name not in groups:
                ig = InstanceGroup()
                conf = {"name": group_name}
                add_ig = self.client.instanceGroups().insert(
                    project=self.credential.project,
                    zone=zone,
                    body=conf
                ).execute()

                self.wait_operation(
                    zone=zone,
                    operation=add_ig.get('name')
                )

                ig.name = group_name
                ig.zone = zone
                groups.append(ig)

        vip.vip_id = vip.group
        return groups

    def _add_instance_in_group(self, equipments, vip):
        for eq in equipments:
            zone = eq.get('zone')
            instance_uri = "projects/{}/zones/{}/instances/{}".format(
                self.credential.project,
                zone,
                eq.get('name')
            )

            instances = {
                "instances": [
                    {'instance': instance_uri},
                ]
            }

            add_inst_req = self.client.instanceGroups().addInstances(
                project=self.credential.project,
                zone=zone,
                instanceGroup=self.__get_instance_group_name(
                    eq.get('group'),
                    zone
                ),
                body=instances
            )

            # safe fail when try to re-add instances
            try:
                add_inst = add_inst_req.execute()
            except HttpError as ex:
                if (ex.resp.status == 400 and
                   json.loads(ex.content)["error"]["errors"]
                   [0]["reason"] == "memberAlreadyExists"):
                    continue

                raise ex

            self.wait_operation(
                zone=zone,
                operation=add_inst.get('name')
            )
        return True

    def _destroy_healthcheck(self, vip):
        hc = self.client.regionHealthChecks().delete(
            project=self.credential.project,
            region=self.credential.region,
            healthCheck=vip.healthcheck
        ).execute()

        self.wait_operation(
            region=self.credential.region,
            operation=hc.get('name')
        )

        return True

    def _create_healthcheck(self, vip):
        hc_name = "hc-%s" % vip.group
        conf = {
            "checkIntervalSec": 5,
            "description": "",
            "healthyThreshold": 2,
            "httpHealthCheck": {
                "host": "",
                "port": 80,
                "proxyHeader": "NONE",
                "requestPath": "/health-check/",
                "response": "WORKING"
            },
            "logConfig": {
                "enable": False
            },
            "name": hc_name,
            "timeoutSec": 5,
            "region": 'southamerica-east1',
            "type": "HTTP",
            "unhealthyThreshold": 2
        }

        hc = self.client.regionHealthChecks().insert(
            project=self.credential.project,
            region=self.credential.region,
            body=conf
        ).execute()

        self.wait_operation(
            region=self.credential.region,
            operation=hc.get('name')
        )

        return hc_name

    def _destroy_backend_service(self, vip):
        bs = self.client.regionBackendServices().delete(
            project=self.credential.project,
            region=self.credential.region,
            backendService=vip.backend_service
        ).execute()

        self.wait_operation(
            region=self.credential.region,
            operation=bs.get('name')
        )

        return True

    def _create_backend_service(self, vip):
        bs_name = "bs-%s" % vip.group
        healthcheck_uri = "regions/%s/healthChecks/%s" % (
            self.credential.region,
            vip.healthcheck
        )

        instance_group_uri = []
        for ig in InstanceGroup.objects.filter(vip=vip):
            uri = "zones/%s/instanceGroups/%s" % (
                ig.zone,
                ig.name
            )
            instance_group_uri.append(uri)

        conf = {
            "name": bs_name,
            "backends": [{'group': x} for x in instance_group_uri],
            "loadBalancingScheme": "INTERNAL",
            "healthChecks": [healthcheck_uri],
            "protocol": "TCP",
            # "port": 3306
        }

        bs = self.client.regionBackendServices().insert(
            project=self.credential.project,
            region=self.credential.region,
            body=conf
        ).execute()

        self.wait_operation(
            region=self.credential.region,
            operation=bs.get('name')
        )

        return bs_name

    def _destroy_forwarding_rule(self, vip):
        fr = self.client.forwardingRules().delete(
            project=self.credential.project,
            region=self.credential.region,
            forwardingRule=vip.forwarding_rule
        ).execute()

        self.wait_operation(
            region=self.credential.region,
            operation=fr.get('name')
        )

        return True

    def _create_forwarding_rule(self, vip):
        fr_name = "fr-%s" % vip.group
        backend_service_uri = "regions/%s/backendServices/%s" % (
            self.credential.region,
            vip.backend_service
        )

        ip_uri = "regions/%s/addresses/%s" % (
            self.credential.region,
            vip.vip_ip_name
        )

        conf = {
            "name": fr_name,
            "loadBalancingScheme": "INTERNAL",
            "IPProtocol": "TCP",
            "ports": ["3306"],
            "IPAddress": ip_uri,
            'subnetwork': self.credential.subnetwork,
            "networkTier": "PREMIUM",
            "backendService": backend_service_uri,
            "allowGlobalAccess": True
        }

        fr = self.client.forwardingRules().insert(
            project=self.credential.project,
            region=self.credential.region,
            body=conf
        ).execute()

        self.wait_operation(
            region=self.credential.region,
            operation=fr.get('name')
        )

        return fr_name

    def _destroy_allocate_ip(self, vip):
        ip = self.client.addresses().delete(
            project=self.credential.project,
            region=self.credential.region,
            address=vip.vip_ip_name
        ).execute()

        self.wait_operation(
            operation=ip.get('name'),
            region=self.credential.region
        )

        return True

    def _allocate_ip(self, vip):
        ip_name = "%s-lbip" % vip.group

        conf = {
            'subnetwork': self.credential.subnetwork,
            'addressType': 'INTERNAL',
            'name': ip_name
        }
        address = self.client.addresses().insert(
            project=self.credential.project,
            region=self.credential.region,
            body=conf
        ).execute()

        self.wait_operation(
            operation=address.get('name'),
            region=self.credential.region
        )

        ip_metadata = self.get_internal_static_ip(ip_name)

        return {'name': ip_name, 'address': ip_metadata.get('address')}

    def get_internal_static_ip(self, ip_name):
        return self.client.addresses().get(
            project=self.credential.project,
            region=self.credential.region,
            address=ip_name
        ).execute()
