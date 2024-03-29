from pymongo import MongoClient, ReturnDocument
from vip_provider.settings import MONGODB_PARAMS, MONGODB_DB

from dbaas_base_provider.baseCredential import BaseCredential


class CredentialMongoDB(BaseCredential):

    provider_type = "vip_provider"

    def __init__(self, provider, environment):
        super(CredentialMongoDB, self).__init__(
            provider,
            environment
        )
        self.MONGODB_PARAMS = MONGODB_PARAMS
        self.MONGODB_DB = MONGODB_DB


class CredentialBase(CredentialMongoDB):

    def __init__(self, provider, environment, engine=None):
        super(CredentialBase, self).__init__(provider, environment)
        self.engine = engine

    def get_content(self):
        content = self.credential.find_one({
            "provider": self.provider,
            "environment": self.environment,
        })
        if content:
            return content

        raise NotImplementedError("No {} credential for {}".format(
            self.provider, self.environment
        ))

    @property
    def content(self):
        if not self._content:
            self._content = self.get_content()
        return super(CredentialBase, self).content

    def get_by(self, **kwargs):
        return self.credential.find(dict(provider=self.provider, **kwargs))

    def all(self, **kwargs):
        return self.get_by()

    def delete(self):
        return self.credential.remove({
            'provider': self.provider,
            'environment': self.environment
        })

    @property
    def _zones_field(self):
        raise NotImplementedError

    def __get_zones(self, **filters):
        all_zones = self._zones_field
        filtered_zones = {}
        for zone_key in all_zones.keys():
            zone_val = all_zones[zone_key]
            valid = True
            for key, value in filters.items():
                if zone_val[key] != value:
                    valid = False
                    break

            if valid:
                filtered_zones[zone_key] = zone_val

        return filtered_zones

    @property
    def all_zones(self):
        return self.__get_zones()

    @property
    def zones(self):
        return self.__get_zones(active=True)

    @property
    def zone(self):
        if self._zone:
            return self._zone
        return self._get_zone()

    @zone.setter
    def zone(self, zone):
        zones = list(self.__get_zones(name=zone).keys())
        self._zone = zones[0]

    def zone_by_id(self, zone_id):
        zones = self.__get_zones(id=zone_id)
        zone_id, values = zones.popitem()
        return values['name']

    def get_next_zone_from(self, zone_name):
        zones = list(self.zones.keys())
        try:
            base_index = zones.index(zone_name)
        except ValueError:
            next_index = 0
        else:
            next_index = base_index + 1
            if next_index >= len(zones):
                next_index = 0

        return zones[next_index]


class CredentialAdd(CredentialMongoDB):
    def __init__(self, provider, environment, content):
        super(CredentialAdd, self).__init__(provider, environment)
        self._content = content

    def save(self):
        return self.credential.find_one_and_update(
            {
                'provider': self.provider,
                'environment': self.environment
            },
            {'$set': dict(
                provider=self.provider,
                environment=self.environment,
                **self.content
            )},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

    def delete(self):
        return self.credential.delete_one({
            'provider': self.provider, 'environment': self.environment
        })

    @property
    def valid_fields(self):
        raise NotImplementedError

    def is_valid(self):
        error = "Required fields {}".format(self.valid_fields)
        if len(self.valid_fields) != len(self.content.keys()):
            return False, error

        for field in self.valid_fields:
            if field not in self.content:
                return False, error

        return True, ''
