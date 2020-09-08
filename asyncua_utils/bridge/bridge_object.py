from asyncua_utils.server import server_from_yaml
import yaml
import logging
import asyncio
import asyncua
from asyncua_utils.bridge.subscription import SubscriptionHandler
from asyncua_utils.bridge import clone_and_subscribe
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256
_logger = logging.getLogger('asyncua')


class Bridge:
    def __init__(self):
        self.server = None
        self.connections = {}

    @classmethod
    async def from_yaml(cls, server_config_yaml, bridge_config_yaml):
        bridge_obj = cls()
        bridge_obj.server = await server_from_yaml(server_config_yaml)

        specification = yaml.load(open(bridge_config_yaml, 'r'), Loader=yaml.SafeLoader)
        for namespace in specification:
            await bridge_obj.make_connection_to_downstream(namespace)
        return bridge_obj

    async def make_connection_to_downstream(self, connection_dict):

        if connection_dict.get('client'):
            await connection_dict['client'].disconnect()

        namespace_idx = await self.server.register_namespace(connection_dict['namespace'])
        _logger.warning('before definition')
        downstream_client = asyncua.Client(url=connection_dict['url'])
        _logger.warning('after definition')

        if connection_dict.get('bridge_certificate'):
            await downstream_client.set_security(SecurityPolicyBasic256Sha256,
                                                 certificate_path=connection_dict['bridge_certificate'],
                                                 private_key_path=connection_dict['bridge_private_key'],
                                                 server_certificate_path=connection_dict['server_certificate'])
        _logger.warning('before connection')
        await downstream_client.connect()
        _logger.warning('after connection')
        sub_handler = SubscriptionHandler(downstream_client, self.server)
        _logger.warning(f"{sub_handler._server == self.server}")

        subscription = await downstream_client.create_subscription(5, sub_handler)
        await clone_and_subscribe(
            downstream_client, connection_dict['nodes'], f'ns={namespace_idx};',
            self.server.nodes.objects, sub_handler, subscription, namespace_idx
        )
        sub_handler.subscribe_to_writes()


        connection_information = {
            'client': downstream_client,
            'namespace_idx': namespace_idx,
            'sub_handler': sub_handler,
            'subscription': subscription,
            **connection_dict
        }

        self.connections[connection_dict['namespace']] = connection_information

    async def maintain_connections(self):
        for namespace, connection_dict in self.connections.items():
            protocol = connection_dict['client'].uaclient.protocol
            if protocol.state == protocol.CLOSED:
                _logger.exception(f"{connection_dict['namespace']} connection closed and is being rebooted")
                exit(1)
                # await asyncio.sleep(5)
                # await self.make_connection_to_downstream(connection_dict)
