# -*- coding: utf-8 -*-
from mongoengine import Document, StringField, IntField, ReferenceField, CASCADE


class Vip(Document):
    port = IntField(required=True)
    group = StringField(max_length=50, required=True)
    vip_id = StringField(max_length=300, required=True)
    vip_ip = StringField(required=True)
    pool_id = StringField(required=False)
    target_group_id = StringField(required=False)
    dscp = IntField(required=False)

    # def set_group(self, group):
    #     self.group = group
    #     pair = Vip.objects(group=group).first()
    #     if pair:
    #         self.resource_id = pair.resource_id

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
            'target_group_id': self.target_group_id
        }
