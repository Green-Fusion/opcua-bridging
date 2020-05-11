import logging
import asyncio

from asyncua import Client

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('asyncua')

PLC_url = "opc.tcp://plc:4840/freeopcua/server/"
cloud_url = "opc.tcp://cloud:4840/freeopcua/server/"


async def main():
    client_PLC = Client(url=PLC_url)
    client_cloud = Client(url=cloud_url)
    await client_PLC.connect()
    await client_cloud.connect()
    obj_PLC = await client_PLC.nodes.root.get_child(['0:Objects', '0:MyObject', '0:MyVariable'])
    obj_cloud = await client_cloud.nodes.root.get_child(['0:Objects', '0:ExamplePLC', '0:MyObject', '0:MyVariable'])

    for i in range(10):
        await asyncio.sleep(3)
        PLC_val = await obj_PLC.get_value()
        cloud_val = await obj_cloud.get_value()
        assert abs(PLC_val - cloud_val) < 0.3

if __name__ == '__main__':
    asyncio.run(main())
