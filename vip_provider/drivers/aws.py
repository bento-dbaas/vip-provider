from libcloud.loadbalancer.types import State
from libcloud.loadbalancer.drivers.elb import ElasticLBDriver, ELBConnection, findtext, findall, LoadBalancer, ELBResponse

VERSION = '2015-12-01'
ROOT = '/%s/' % (VERSION)
NS = 'http://elasticloadbalancing.amazonaws.com/doc/%s/' % (VERSION, )


class NLBResponse(ELBResponse):
    """
    Amazon NLB response class.
    """
    namespace = NS


class NLBConnection(ELBConnection):
    version = '2015-12-01'
    responseCls = NLBResponse


class TargetGroup(object):
    """
    Provide a common interface for handling Target Groups.
    """

    def __init__(self, id, name, port, driver, vpc_id, extra=None):
        self.id = str(id) if id else None
        self.name = name
        self.port = port
        self.driver = driver
        self.vpc_id = vpc_id
        self.extra = extra or {}

    def __repr__(self):
        return ('<TargetGroup: id=%s, name=%s, vpc_id=%s '
                'port=%s>' % (self.id, self.name, self.vpc_id,
                              self.port))


class LBListener(object):
    """
    Provide a common interface for handling Load Balancer Listener.
    """

    def __init__(self, id, port, protocol, load_balancer_arn,
                 target_group_arn, driver, extra=None):
        self.id = str(id) if id else None
        self.port = port
        self.protocol = protocol
        self.load_balancer_arn = load_balancer_arn
        self.target_group_arn = target_group_arn
        self.driver = driver
        self.extra = extra or {}

    def __repr__(self):
        return '<LBListener: id={}, port={}, protocol={}'.format(self.id, self.port, self.protocol)


class NetworkLBDriver(ElasticLBDriver):
    connectionCls = NLBConnection

    def destroy_balancer(self, balancer):
        params = {
            'Action': 'DeleteLoadBalancer',
            'LoadBalancerArn': balancer.id
        }
        self.connection.request(ROOT, params=params)
        return True

    def destroy_target_group(self, target_group):
        params = {
            'Action': 'DeleteTargetGroup',
            'TargetGroupArn': target_group.id
        }
        self.connection.request(ROOT, params=params)
        return True

    def get_balancer(self, balancer_id, ex_fetch_tags=False):
        params = {
            'Action': 'DescribeLoadBalancers',
            'LoadBalancerArns.member.1': balancer_id
        }
        data = self.connection.request(ROOT, params=params).object
        balancer = self._to_balancers(data)[0]

        if ex_fetch_tags:
            balancer = self._ex_populate_balancer_tags(balancer)

        return balancer

    def get_target_healthy(self, target_group_id):
        params = {
            'Action': 'DescribeTargetHealth',
            'TargetGroupArn': target_group_id
        }
        data = self.connection.request(ROOT, params=params).object
        state = self._to_states(data)

        return state


    def get_target_group(self, balancer_id=None, target_group_id=None, ex_fetch_tags=False):
        params = {
            'Action': 'DescribeTargetGroups',
        }
        if not balancer_id and not target_group_id:
            raise Exception('U must provider the id of balancer or target group')
        if target_group_id:
            params['TargetGroupArns.member.1'] = target_group_id
        elif balancer_id:
            params['LoadBalancerArn'] = balancer_id

        data = self.connection.request(ROOT, params=params).object
        balancer = self._to_target_groups(data)[0]

        if ex_fetch_tags:
            balancer = self._ex_populate_balancer_tags(balancer)

        return balancer

    def _to_balancers(self, data):
        xpath = 'DescribeLoadBalancersResult/LoadBalancers/member'
        return [self._to_balancer(el)
                for el in findall(element=data, xpath=xpath, namespace=NS)]

    def _to_states(self, data):
        xpath = 'DescribeTargetHealthResult/TargetHealthDescriptions/member'
        for el in findall(element=data, xpath=xpath, namespace=NS):
            state = self._to_state(el)
            if state == 'healthy':
                return True
        return False

    def _to_balancer(self, el):
        name = findtext(element=el, xpath='LoadBalancerName', namespace=NS)
        dns_name = findtext(el, xpath='DNSName', namespace=NS)
        state = findtext(el, xpath='State/Code', namespace=NS)
        load_balancer_arn = findtext(el, xpath='LoadBalancerArn', namespace=NS)
        balancer = LoadBalancer(
            id=load_balancer_arn,
            name=name,
            state=state,
            ip=dns_name,
            port=None,
            driver=self.connection.driver
        )
        balancer._members = []
        return balancer

    def _to_state(self, el):
        return findtext(el, xpath='TargetHealth/State', namespace=NS)

    def _to_target_groups(self, data):
        xpath = 'DescribeTargetGroupsResult/TargetGroups/member'
        return [self._to_target_group(el)
                for el in findall(element=data, xpath=xpath, namespace=NS)]

    def _to_target_group(self, el):
        name = findtext(element=el, xpath='TargetGroupName', namespace=NS)
        vpc_id = findtext(el, xpath='VpcId', namespace=NS)
        port = findtext(el, xpath='Port', namespace=NS)
        target_group_arn = findtext(el, xpath='TargetGroupArn', namespace=NS)
        target_group = TargetGroup(
            id=target_group_arn,
            name=name,
            port=port,
            driver=self.connection.driver,
            vpc_id=vpc_id,
            extra={
                'target_group_arn': target_group_arn
            }
        )
        return target_group

    def create_balancer(self, name, port, subnets):
        params = {
            'Action': 'CreateLoadBalancer',
            'Name': name,
            'Scheme': 'internal',
            'Type': 'network'
        }
        subnet_tmpl = 'Subnets.member.{}'
        for pos, subnet in enumerate(subnets):
            params[subnet_tmpl.format(pos+1)] = subnet

        data = self.connection.request(ROOT, params=params).object

        response_xpath = 'CreateLoadBalancerResult/LoadBalancers/member/{}'
        load_balancer_arn = findtext(element=data, xpath=response_xpath.format('LoadBalancerArn'), namespace=NS)
        balancer = LoadBalancer(
            id=load_balancer_arn,
            name=name,
            state=State.PENDING,
            ip=findtext(element=data, xpath=response_xpath.format('DNSName'), namespace=NS),
            port=port,
            driver=self.connection.driver,
            extra={
                'load_balancer_arn': findtext(
                    element=data,
                    xpath=load_balancer_arn,
                    namespace=NS
                )
            }
        )
        balancer._members = []
        return balancer

    def create_target_group(self, name, port, protocol, vpc_id,
                            healthcheck_config, healthy_threshold_count,
                            unhealthy_threshold_count, target_type):
        params = {
            'Action': 'CreateTargetGroup',
            'Name': name,
            'Port': port,
            'Protocol': protocol,
            'TargetType': target_type,
            'VpcId': vpc_id,
            'HealthyThresholdCount': healthy_threshold_count,
            'UnhealthyThresholdCount': unhealthy_threshold_count
        }

        params.update(healthcheck_config)

        data = self.connection.request(ROOT, params=params).object

        response_xpath = 'CreateTargetGroupResult/TargetGroups/member/{}'
        target_group_arn = findtext(
            element=data,
            xpath=response_xpath.format('TargetGroupArn'),
            namespace=NS
        )
        target_group = TargetGroup(
            id=target_group_arn,
            name=name,
            port=port,
            driver=self.connection.driver,
            vpc_id=vpc_id,
            extra={
                'target_group_arn': target_group_arn
            }
        )
        return target_group

    def create_listener(self, load_balancer, target_group, protocol, port):

        load_balancer_arn = load_balancer.id
        target_group_arn = target_group.id

        params = {
            'Action': 'CreateListener',
            'LoadBalancerArn': load_balancer_arn,
            'Protocol': protocol,
            'Port': port,
            'DefaultActions.member.1.Type': 'forward',
            'DefaultActions.member.1.TargetGroupArn': target_group_arn
        }

        data = self.connection.request(ROOT, params=params).object

        response_xpath = 'CreateListenerResult/Listeners/member/{}'
        listener_arn = findtext(
            element=data,
            xpath=response_xpath.format('ListenerArn'),
            namespace=NS
        )
        listener = LBListener(
            id=listener_arn,
            port=port,
            protocol=protocol,
            load_balancer_arn=load_balancer_arn,
            target_group_arn=target_group_arn,
            driver=self.connection.driver,
            extra={'listener_arn': listener_arn}
        )
        return listener

    def set_subnet(self, balancer_id, subnets):
        params = {
            'Action': 'SetSubnets',
            'LoadBalancerArn': balancer_id,
        }

        subnet_tmpl = 'Subnets.member.{}'
        for pos, subnet in enumerate(subnets):
            params[subnet_tmpl.format(pos+1)] = subnet

        self.connection.request(ROOT, params=params).object

        return True

    def register_targets(self, target_group_id, instances):
        params = {
            'Action': 'RegisterTargets',
            'TargetGroupArn': target_group_id,
        }

        targets_tmpl = 'Targets.member.{}.{}'
        for pos, instance in enumerate(instances):
            params[targets_tmpl.format(pos+1, 'Id')] = instance['id']
            params[targets_tmpl.format(pos+1, 'Port')] = instance['port']

        self.connection.request(ROOT, params=params).object

        return True

    def deregister_targets(self, target_group_id, instances):
        params = {
            'Action': 'DeregisterTargets',
            'TargetGroupArn': target_group_id,
        }

        targets_tmpl = 'Targets.member.{}.{}'
        for pos, instance in enumerate(instances):
            params[targets_tmpl.format(pos+1, 'Id')] = instance['id']

        self.connection.request(ROOT, params=params).object

        return True
