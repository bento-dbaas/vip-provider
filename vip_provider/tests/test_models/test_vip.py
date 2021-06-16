from unittest import TestCase
from vip_provider.models import Vip


class PropertiesTestCase(TestCase):

    def setUp(self):
        self.vip = Vip()
        self.vip_data = {
            'id': 11,
            'group': 'fake_group'
        }
        self.vip._data = self.vip_data

    def test_return_normal_fields(self):
        my_dict = self.vip._data
        self.assertIn('id', my_dict)
        self.assertIn('group', my_dict)
