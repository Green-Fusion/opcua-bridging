import logging
import os

from asyncua import Client
import asyncio
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256
from asyncua_utils.server import server_from_yaml
from asyncua_utils.bridge.yaml import produce_full_bridge_yaml

logging.basicConfig(level=logging.WARNING)
_logger = logging.getLogger('asyncua')

PLC_url = os.environ['OPC_PLC_URL']
secure = os.environ.get('secure')
# PLC_url_2 = os.environ['OPC_PLC_URL_2']
cloud_url = "opc.tcp://cloud:4840/freeopcua/server/"


async def main():
    # setup our serverclone_and_subscribe(client_node, server_node, sub_handler)
    client = Client(url=PLC_url)
    if secure:
        cloud_cert = '/credentials/cloud_cert.der'
        cloud_private_key = '/credentials/cloud_private_key.pem'
        server_cert = '/credentials/PLC_cert.der'
        await client.set_security(
            SecurityPolicyBasic256Sha256,
            certificate=cloud_cert,
            private_key=cloud_private_key,
            server_certificate=server_cert
        )
    await client.connect()

    # client2 = Client(url=PLC_url_2)
    #
    # await client2.connect()

    node_1_client = client.nodes.objects
    # node_2_client = client2.nodes.objects

    bridge_dict = {'nodes': node_1_client, 'name': 'plc_1', 'url': PLC_url}
    if secure:
        bridge_dict.update({'bridge_certificate': cloud_cert,
                 'bridge_private_key': cloud_private_key, 'server_certificate': server_cert})
    await produce_full_bridge_yaml([
        bridge_dict,
    ], '/appdata/test_yaml/test.yaml')

if __name__ == '__main__':
    _logger.warning('got here')
    asyncio.run(main())
