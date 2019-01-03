from vip_provider.credentials.base import CredentialBase, CredentialAdd


class CredentialAWS(CredentialBase):

    @property
    def health_check_interval_seconds(self):
        return self.content['health_check_interval_seconds']

    @property
    def health_check_path(self):
        return self.content['health_check_path']

    @property
    def health_check_port(self):
        return self.content['health_check_port']

    @property
    def health_check_protocol(self):
        return self.content['health_check_protocol']

    @property
    def health_check_timeout_seconds(self):
        return self.content['health_check_timeout_seconds']

    @property
    def access_id(self):
        return self.content['access_id']

    @property
    def secret_key(self):
        return self.content['secret_key']

    @property
    def region(self):
        return self.content['region']

    @property
    def subnets(self):
        return self.content['subnets']

    @property
    def vpc_id(self):
        return self.subnets[self.zone]['vpc_id']

    @property
    def _zones_field(self):
        return self.subnets

    def before_create_vip(self):
        self._zone = self._get_zone()

    def after_create_vip(self):
        existing = self.exist_node()
        if not existing:
            self.collection_last.update_one(
                {"latestUsed": True, "environment": self.environment},
                {"$set": {"zone": self.zone}}, upsert=True
            )

        self.collection_last.update(
            {"environment": self.environment},
            {"$set": {"zone": self.zone}}, upsert=True
        )

    def remove_last_used_for(self):
        self.collection_last.delete_one({
            "environment": self.environment
        })

    @property
    def collection_last(self):
        return self.db["ec2_zones_last"]

    def exist_node(self):
        return self.collection_last.find_one({
            "environment": self.environment
        })

    def last_used_zone(self):
        return self.collection_last.find_one({
            "latestUsed": True, "environment": self.environment
        })

    def _get_zone(self):
        exist = self.exist_node()
        if exist:
            return self.get_next_zone_from(exist["zone"])

        latest_used = self.last_used_zone()
        if latest_used:
            return self.get_next_zone_from(latest_used["zone"])

        resp = list(self.zones.keys())
        return resp[0]

class CredentialAddAWS(CredentialAdd):

    @property
    def valid_fields(self):
        return [
            'access_id', 'secret_key', 'region'
        ]
