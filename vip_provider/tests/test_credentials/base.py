from collections import OrderedDict
from mock import patch
from vip_provider.settings import MONGODB_HOST, MONGODB_PORT, MONGODB_USER, \
    MONGODB_PWD
from vip_provider.credentials.base import CredentialAdd, CredentialBase
from vip_provider.tests.test_credentials import (
    CredentialAddFake,
    CredentialBaseFake,
    FakeMongoDB)


PROVIDER = "fake"
ENVIRONMENT = "dev"
ENGINE = "redis"
FAKE_CERT_PATH = "/path/to/certs/"
GROUP = "fake-group"


class TestBaseProvider(object):

    def tearDown(self):
        FakeMongoDB.clear()

    def test_base_content(self):
        credential_add = CredentialAddFake(
            PROVIDER, ENVIRONMENT, {"fake": "info"}
        )
        credential_add.save()
        credential = CredentialBaseFake(PROVIDER, ENVIRONMENT, ENGINE)
        self.assertIsNone(credential._content)
        self.assertEqual(credential.content, credential._content)
        self.assertIsNotNone(credential.content)

    def test_base_content_empty(self):
        credential = CredentialBaseFake(PROVIDER, ENVIRONMENT + "-new", ENGINE)
        self.assertIsNone(credential._content)
        self.assertRaises(NotImplementedError, credential.get_content)

    @patch('vip_provider.credentials.base.MongoClient')
    def test_mongo_db_connection(self, mongo_client):
        credential = CredentialBase(PROVIDER, ENVIRONMENT, ENGINE)
        self.assertIsNotNone(credential.credential)
        mongo_client.assert_called_once_with(
            host=MONGODB_HOST, port=MONGODB_PORT,
            username=MONGODB_USER, password=MONGODB_PWD,
            document_class=OrderedDict
        )

    @patch('vip_provider.credentials.base.CredentialAdd.credential')
    def test_delete(self, credential):
        env = "env"
        provider = "fake"
        CredentialAdd(provider, env, {}).delete()
        credential.delete_one.assert_called_once_with({
            "environment": env, "provider": provider
        })
