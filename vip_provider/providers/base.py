# -*- coding: utf-8 -*-
from vip_provider.models import Vip


class ProviderBase(object):

    def __init__(self, environment):
        self.environment = environment
        self._client = None
        self._credential = None

    @property
    def client(self):
        if not self._client:
            self._client = self.build_client()
        return self._client

    @property
    def credential(self):
        if not self._credential:
            self._credential = self.build_credential()
        return self._credential

    def credential_add(self, content):
        credential_cls = self.get_credential_add()
        credential = credential_cls(self.provider, self.environment, content)
        is_valid, error = credential.is_valid()
        if not is_valid:
            return False, error

        try:
            insert = credential.save()
        except Exception as e:
            return False, str(e)
        else:
            return True, insert.get('_id')

    @property
    def provider(self):
        return self.get_provider()

    @classmethod
    def get_provider(cls):
        raise NotImplementedError

    def build_client(self):
        raise NotImplementedError

    def build_credential(self):
        raise NotImplementedError

    def get_credential_add(self):
        raise NotImplementedError

    def create_vip(self, group, port, equipments, vip_dns):
        vip = Vip()
        vip.port = port
        vip.group = group
        vip.equipments = equipments
        vip.vip_dns = vip_dns
        self._create_vip(vip)
        vip.save()

        return vip

    def add_real(self, *args, **kw):
        return self._add_real(*args, **kw)

    def _add_real(self, *args, **kw):
        raise NotImplemented()

    def remove_real(self, *args, **kw):
        return self._remove_real(*args, **kw)

    def _remove_real(self, *args, **kw):
        raise NotImplemented()

    def update_vip_reals(self, *args, **kw):
        return self._update_vip_reals(*args, **kw)

    def _update_vip_reals(self, *args, **kw):
        raise NotImplementedError

    def _create_vip(self, vip):
        raise NotImplementedError

    def delete_vip(self, identifier):
        vip = Vip.objects(id=identifier).get()
        self._delete_vip(vip)
        vip.delete()

    def _delete_vip(self, vip):
        raise NotImplementedError

    def get_vip(self, identifier):
        try:
            return Vip.objects(id=identifier).get()
        except Vip.DoesNotExist:
            pass
        return None
