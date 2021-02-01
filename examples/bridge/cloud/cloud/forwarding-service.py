import logging
import asyncio
import os

from asyncua import Client

from asyncua_utils.bridge import create_simple_bridge
from asyncua_utils.bridge.subscription import SubscriptionHandler
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256
from asyncua_utils.server import server_from_yaml

logging.basicConfig(level=logging.WARNING)
_logger = logging.getLogger('asyncua')

PLC_url = os.environ['OPC_PLC_URL']
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

    obj_1 = await server.nodes.objects.add_object(0, 'ExamplePLC')
    obj_2 = await server.nodes.objects.add_object(1, 'TSPLC')
    node_1_client = await client.nodes.objects.get_child(['0:MyObject'])
    node_2_client = await client.nodes.objects.get_child(['0:TimeSeries'])

    client_var = await client.nodes.root.get_child(['0:Objects', '0:MyObject', '0:MyVariable'])
    handler = await SubscriptionHandler(client, server)

    subscription = await client.create_subscription(5, handler)

    await create_simple_bridge(node_1_client, obj_1, handler, subscription, client, node_id_prefix='ns=1;')
    await create_simple_bridge(node_2_client, obj_2, handler, subscription, client, node_id_prefix='ns=2;')
    handler.subscribe_to_writes()
    nodes = [client_var]
    async with server:
        # await subscription.subscribe_data_change(nodes)
        await asyncio.sleep(100)
        await subscription.delete()
        await asyncio.sleep(1)
        print(await client_var.read_value())


if __name__ == '__main__':
    asyncio.run(main())
