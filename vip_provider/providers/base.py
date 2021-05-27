# -*- coding: utf-8 -*-
from vip_provider.models import Vip

from dbaas_base_provider.baseProvider import BaseProvider


class ProviderBase(BaseProvider):

    provider_type = "vip_provider"

    def __init__(self, environment, engine=None, auth_info=None):
        super(ProviderBase, self).__init__(
            environment,
            engine=engine,
            auth_info=None
        )

    def create_vip(self, group, port, equipments, vip_dns):
        vip = Vip()
        vip.port = port
        vip.group = group
        vip.equipments = equipments
        vip.vip_dns = vip_dns
        self._create_vip(vip)
        vip.save()

        return vip

    def create_instance_group(self, group, port, vip_dns, equipments):
        vip = Vip()
        vip.port = port
        vip.group = group
        vip.vip_dns = vip_dns
        instance_groups = self._create_instance_group(
            vip, equipments)

        vip.vip_ip = ""
        vip.save()

        for ig in instance_groups:
            ig.vip = vip
            ig.save()

        return vip, instance_groups

    def add_instance_in_group(self, equipments, vip):
        vip_obj = Vip.objects(pk=vip).get()
        return self._add_instance_in_group(equipments, vip_obj)

    def create_healthcheck(self, vip):
        vip_obj = Vip.objects(pk=vip).get()
        hc_name = self._create_healthcheck(vip_obj)

        vip_obj.healthcheck = hc_name

        vip_obj.save()
        return hc_name
    
    def destroy_healthcheck(self, vip):
        vip_obj = Vip.objects(pk=vip).get()
        self._destroy_healthcheck(vip_obj)

        vip_obj.healthcheck = None

        vip_obj.save()
        return True

    def create_backend_service(self, vip):
        vip_obj = Vip.objects(pk=vip).get()
        bc_name = self._create_backend_service(vip_obj)

        vip_obj.backend_service = bc_name
        vip_obj.save()
        return bc_name

    def destroy_backend_service(self, vip):
        vip_obj = Vip.objects(pk=vip).get()
        self._destroy_backend_service(vip_obj)

        vip_obj.backend_service = None
        vip_obj.save()
        return True

    def create_forwarding_rule(self, vip):
        vip_obj = Vip.objects(pk=vip).get()
        fr_name = self._create_forwarding_rule(vip_obj)

        vip_obj.forwarding_rule = fr_name
        vip_obj.save()
        return fr_name

    def destroy_forwarding_rule(self, vip):
        vip_obj = Vip.objects(pk=vip).get()
        self._destroy_forwarding_rule(vip_obj)

        vip_obj.forwarding_rule = None
        vip_obj.save()
        return True

    def allocate_ip(self, vip):
        vip_obj = Vip.objects(pk=vip).get()
        ip_info = self._allocate_ip(vip_obj)

        vip_obj.vip_ip_name = ip_info.get('name')
        vip_obj.vip_ip = ip_info.get('address')
        vip_obj.save()
        return ip_info

    def destroy_allocate_ip(self, vip):
        vip_obj = Vip.objects(pk=vip).get()
        self._destroy_allocate_ip(vip_obj)

        vip_obj.vip_ip = ""
        vip_obj.vip_ip_name = None
        vip_obj.save()
        return True

    def add_real(self, *args, **kw):
        return self._add_real(*args, **kw)

    def _add_real(self, *args, **kw):
        raise NotImplementedError

    def remove_real(self, *args, **kw):
        return self._remove_real(*args, **kw)

    def _remove_real(self, *args, **kw):
        raise NotImplementedError

    def update_vip_reals(self, *args, **kw):
        return self._update_vip_reals(*args, **kw)

    def _update_vip_reals(self, *args, **kw):
        raise NotImplementedError

    def _create_vip(self, vip):
        raise NotImplementedError

    def _create_instance_group(self, *args, **kwargs):
        raise NotImplementedError

    def _add_instance_in_group(self, *args, **kwargs):
        raise NotImplementedError

    def _create_healthcheck(self, vip):
        raise NotImplementedError

    def _destroy_healthcheck(self, vip):
        raise NotImplementedError

    def _create_backend_service(self, vip):
        raise NotImplementedError

    def _destroy_backend_service(self, vip):
        raise NotImplementedError

    def _create_forwading_rule(self, vip):
        raise NotImplementedError

    def _destroy_forwarding_rule(self, vip):
        raise NotImplementedError

    def _allocate_ip(self, vip):
        raise NotImplementedError

    def _destroy_allocate_ip(self, vip):
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
