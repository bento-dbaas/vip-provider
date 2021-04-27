from collections import namedtuple
from mock import MagicMock
from vip_provider.models import Vip


FAKE_ENGINE = namedtuple(
    'FakeEngine', 'id name'
    )(
        'fake_engine_id',
        'fake_engine_name'
    )

FAKE_VIP = MagicMock(spec=Vip)
FAKE_VIP.id = 'fake_id'
FAKE_VIP.group = 'FAKE_VIP_group'
FAKE_VIP.vip_id = 'FAKE_VIP_id'
FAKE_VIP.vip_ip = 'FAKE_IP_ip'
