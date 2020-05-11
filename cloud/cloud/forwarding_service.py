import logging
import asyncio

from asyncua import Server, Client

from cloud.node_walking import clone_and_subscribe
from cloud.subscription_handler import SubscriptionHandler

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('asyncua')

PLC_url = "opc.tcp://plc:4840/freeopcua/server/"
cloud_url = "opc.tcp://cloud:4840/freeopcua/server/"


async def main():
    # setup our serverclone_and_subscribe(client_node, server_node, sub_handler)
    server = Server()
    client = Client(url=PLC_url)
    await server.init()
    await client.connect()
    obj_1 = await server.nodes.objects.add_object(0, 'ExamplePLC')
    client_1 = await client.nodes.objects.get_child(['0:MyObject'])

    server.set_endpoint(cloud_url)
    client_var = await client.nodes.root.get_child(['0:Objects', '0:MyObject', '0:MyVariable'])
    handler = SubscriptionHandler(client, server)

    await clone_and_subscribe(client_1, obj_1, handler)
    # setup our own namespace, not really necessary but should as spec
    subscription = await client.create_subscription(5, handler)
    nodes = [client_var]
    async with server:
        await subscription.subscribe_data_change(nodes)
        await asyncio.sleep(100)

        await subscription.delete()

        await asyncio.sleep(1)
        print(await client_var.read_value())


if __name__ == '__main__':
    asyncio.run(main())
