import logging
import asyncio
import os

from asyncua import Client

from asyncua_utils.bridge import create_simple_bridge
from asyncua_utils.bridge.subscription import SubscriptionHandler
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256
from asyncua_utils.server import server_from_yaml
from asyncua_utils.bridge.yaml import bridge_from_yaml

logging.basicConfig(level=logging.WARNING)
_logger = logging.getLogger('asyncua')

PLC_url = os.environ['OPC_PLC_URL']
PLC_url_2 = os.environ['OPC_PLC_URL_2']
cloud_url = "opc.tcp://cloud:4840/freeopcua/server/"


async def main():
    # setup our serverclone_and_subscribe(client_node, server_node, sub_handler)
    server = await server_from_yaml('cloud_server_config.yaml')

    client = Client(url=PLC_url)
    await client.set_security(
        SecurityPolicyBasic256Sha256,
        certificate_path='/credentials/cloud_cert.der',
        private_key_path='/credentials/cloud_private_key.pem',
        server_certificate_path='/credentials/PLC_cert.der'
    )
    await client.connect()

    client2 = Client(url=PLC_url_2)

    await client2.connect()

    holder = await bridge_from_yaml(server, '/appdata/test_yaml/test.yaml')
    for sub_hold in holder:
        _logger.warning(sub_hold[0]._client_server_mapping)
    async with server:
        # await subscription.subscribe_data_change(nodes)
        while True:
            await asyncio.sleep(100)

if __name__ == '__main__':
    asyncio.run(main())
