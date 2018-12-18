from pymongo import MongoClient, ReturnDocument
from vip_provider.settings import MONGODB_PARAMS, MONGODB_DB


class CredentialMongoDB(object):

    def __init__(self, provider, environment):
        self.provider = provider
        self.environment = environment
        self._db = None
        self._collection_credential = None
        self._content = None
        self._zone = None

    @property
    def db(self):
        if not self._db:
            client = MongoClient(**MONGODB_PARAMS)
            self._db = client[MONGODB_DB]
        return self._db

    @property
    def credential(self):
        if not self._collection_credential:
            self._collection_credential = self.db["credentials"]
        return self._collection_credential

    @property
    def content(self):
        return self._content


class CredentialBase(CredentialMongoDB):

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
        return self.credential.find({'provider': self.provider, **kwargs})

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
            {'$set': {
                'provider': self.provider,
                'environment': self.environment,
                **self.content
            }},
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
