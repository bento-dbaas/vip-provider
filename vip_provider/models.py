# -*- coding: utf-8 -*-
from mongoengine import (Document, StringField, ListField,
                         IntField, ReferenceField, CASCADE)


class Vip(Document):
    port = IntField(required=True)
    group = StringField(max_length=50, required=True)
    vip_id = StringField(max_length=300, required=True)
    vip_ip = StringField(required=True)
    pool_id = StringField(required=False)
    target_group_id = StringField(required=False)
    dscp = IntField(required=False)

    # GCP specific fields
    healthcheck = StringField(max_length=50, required=False)
    backend_service = StringField(max_length=50, required=False)
    forwarding_rule = StringField(max_length=50, required=False)
    vip_ip_name = StringField(max_length=50, required=False)
    # def set_group(self, group):
    #     self.group = group
    #     pair = Vip.objects(group=group).first()
    #     if pair:
    #         self.resource_id = pair.resource_id

    # Ingress Provider specific fields
    ingress_provider_region = StringField(required=False)
    ingress_provider_hosts_ips = ListField(required=False)
    ingress_provider_team_name = StringField(required=False)

    @property
    def uuid(self):
        return str(self.pk)

    @property
    def get_json(self):
        return {
            'port': self.port,
            'group': self.group,
            'vip_id': self.vip_id,
            'vip_ip': self.vip_ip,
            'dscp': self.dscp,
            'pool_id': self.pool_id,
            'target_group_id': self.target_group_id,
            'healthcheck': self.healthcheck,
            'backend_service': self.backend_service,
            'forwarding_rule': self.forwarding_rule,
            'vip_ip_name': self.vip_ip_name
        }


class InstanceGroup(Document):
    vip = ReferenceField(Vip, required=True, reverse_delete_rule=CASCADE)
    name = StringField(required=True, max_length=60)
    zone = StringField(required=True, max_length=50)
    meta = {
        'indexes': [
            {'fields': ('name', 'zone'), 'unique': True}
        ]
    }

    @property
    def uuid(self):
        return str(self.pk)

    def to_json(self):
        return {
            'id': self._id,
            'vip': self.vip,
            'name': self.name
        }
