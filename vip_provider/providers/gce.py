from vip_provider.providers.base import ProviderBase
from vip_provider.credentials.gce import CredentialGce, CredentialAddGce
from googleapiclient.errors import HttpError
import httplib2
import google_auth_httplib2

from vip_provider.settings import HTTP_PROXY, TEAM_API_URL
import googleapiclient.discovery
from google.oauth2 import service_account

from dbaas_base_provider.team import TeamClient
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

    def _remove_instance_group(self, instance_group, vip,
                               destroy_vip, only_if_empty=False):
        destroyed = []
        for ig in instance_group:
            if only_if_empty:
                ig_get = self.client.instanceGroups().get(
                    project=self.credential.project,
                    zone=ig.zone,
                    instanceGroup=ig.name
                ).execute()
                if ig_get['size'] > 0:
                    continue

            ig_del = self.get_or_none_resource(
                self.client.instanceGroups,
                project=self.credential.project,
                zone=ig.zone,
                instanceGroup=ig.name
            )
            if ig_del is None:
                continue

            ig_del = self.client.instanceGroups().delete(
                project=self.credential.project,
                zone=ig.zone,
                instanceGroup=ig.name
            ).execute()

            destroyed.append(str(ig.pk))

            self.wait_operation(
                zone=ig.zone,
                operation=ig_del.get('name')
            )
            ig.delete()

        return destroyed

    def _create_instance_group(self, vip, equipments):
        '''create one group to each zone'''
        groups = []
        for eq in equipments:
            zone = eq.get("zone", None)
            group_name = self.__get_instance_group_name(
                vip.group,
                zone
            )
            if group_name not in groups:

                add_ig = self.get_or_none_resource(
                    self.client.instanceGroups,
                    project=self.credential.project,
                    zone=zone,
                    instanceGroup=group_name
                )

                if add_ig is None:
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

                ig = InstanceGroup.objects(
                    name=group_name,
                    zone=zone
                )
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
        hc = self.get_or_none_resource(
            self.client.regionHealthChecks,
            project=self.credential.project,
            region=self.credential.region,
            healthCheck=vip.healthcheck
        )
        if hc is None:
            return True

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
        hc = self.get_or_none_resource(
            self.client.regionHealthChecks,
            project=self.credential.project,
            region=self.credential.region,
            healthCheck=hc_name
        )
        if hc is not None:
            return hc_name

        conf = {
            "checkIntervalSec": 5,
            "description": "",
            "healthyThreshold": 2,
            "httpHealthCheck": {
                "host": "",
                "port": 80,
                "proxyHeader": "NONE",
                "requestPath": "/health-check/foxha/",
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
        bs = self.get_or_none_resource(
            self.client.regionBackendServices,
            project=self.credential.project,
            region=self.credential.region,
            backendService=vip.backend_service
        )
        if bs is None:
            return True

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

    def _update_backend_service(self, vip, instance_groups):
        conf = {}
        instance_group_uri = []
        for ig in instance_groups:
            uri = "zones/%s/instanceGroups/%s" % (
                ig.zone,
                ig.name
            )
            instance_group_uri.append(uri)

        conf = {"backends": [
                {'group': x,
                 "failover": i > 0} for i, x in enumerate(instance_group_uri)]}

        bs = self.client.regionBackendServices().patch(
            project=self.credential.project,
            region=self.credential.region,
            backendService=vip.backend_service,
            body=conf
        ).execute()

        self.wait_operation(
            region=self.credential.region,
            operation=bs.get('name')
        )

        return True

    def _create_backend_service(self, vip):
        bs_name = "bs-%s" % vip.group

        bs = self.get_or_none_resource(
            self.client.regionBackendServices,
            project=self.credential.project,
            region=self.credential.region,
            backendService=bs_name
        )
        if bs is not None:
            return bs_name

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
            "backends": [
                {'group': x,
                 "failover": i > 0} for i, x in enumerate(instance_group_uri)],
            "loadBalancingScheme": "INTERNAL",
            "healthChecks": [healthcheck_uri],
            "protocol": "TCP",
            "failoverPolicy": {
                "disableConnectionDrainOnFailover": True,
                "dropTrafficIfUnhealthy": True,
                "failoverRatio": 0
            }
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
        fr = self.get_or_none_resource(
            self.client.forwardingRules,
            project=self.credential.project,
            region=self.credential.region,
            forwardingRule=vip.forwarding_rule
        )
        if fr is None:
            return True

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

    def _add_tags_in_forwarding_rules(self, vip, **kwargs):
        # add labels with patch
        # forwardint rule does not
        # support add tags on create
        # only add tags on resource update
        team_name = kwargs.get("team_name", None)
        engine_name = kwargs.get("engine_name", None)
        infra_name = kwargs.get("infra_name", None)
        database_name = kwargs.get("database_name", None)

        team_client = TeamClient(
            api_url=TEAM_API_URL, team_name=team_name)

        labels = team_client.make_labels(
            engine_name=engine_name,
            infra_name=infra_name,
            database_name=database_name
        )

        label_fingerprint = self.client\
            .forwardingRules().get(
                project=self.credential.project,
                region=self.credential.region,
                forwardingRule=vip.forwarding_rule
            ).execute().get('labelFingerprint')

        conf = {
            "labelFingerprint": label_fingerprint,
            "labels": labels
        }

        lbl_update = self.client.forwardingRules().setLabels(
            project=self.credential.project,
            region=self.credential.region,
            resource=vip.forwarding_rule,
            body=conf
        ).execute()

        return self.wait_operation(
            region=self.credential.region,
            operation=lbl_update.get('name')
        )

    def _create_forwarding_rule(self, vip, **kwargs):
        fr_name = "fr-%s" % vip.group

        fr = self.get_or_none_resource(
            self.client.forwardingRules,
            project=self.credential.project,
            region=self.credential.region,
            forwardingRule=fr_name
        )
        if fr is not None:
            return fr_name

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
        ip = self.get_or_none_resource(
            self.client.addresses,
            project=self.credential.project,
            region=self.credential.region,
            address=vip.vip_ip_name
        )
        if ip is None:
            return True

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

        address = self.get_or_none_resource(
            self.client.addresses,
            project=self.credential.project,
            region=self.credential.region,
            address=ip_name
        )

        if address is None:
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
