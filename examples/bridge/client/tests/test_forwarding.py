import logging
import asyncio

from asyncua import Client
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256
import pytest
import random

logging.basicConfig(level=logging.WARNING)
_logger = logging.getLogger('asyncua')

PLC_url = "opc.tcp://plc:4840/freeopcua/server/"
cloud_url = "opc.tcp://cloud:4840/freeopcua/server/"


@pytest.fixture()
async def client_PLC():
    client_PLC = Client(url=PLC_url)
    await client_PLC.set_security(
        SecurityPolicyBasic256Sha256,
        certificate_path='/credentials/user_admin_cert.der',
        private_key_path='/credentials/user_admin_private_key.pem',
        server_certificate_path='/credentials/PLC_cert.der'
    )
    return client_PLC


@pytest.fixture()
async def client_cloud():
    client_cloud = Client(url=cloud_url)
    await client_cloud.set_security(
        SecurityPolicyBasic256Sha256,
        certificate_path='/credentials/user_admin_cert.der',
        private_key_path='/credentials/user_admin_private_key.pem',
        server_certificate_path='/credentials/cloud_cert.der'
    )
    return client_cloud


@pytest.mark.asyncio
async def test_forwarding_from_plc(client_PLC, client_cloud):
    async with client_PLC:
        async with client_cloud:
            obj_PLC = await client_PLC.nodes.root.get_child(['0:Objects', '0:MyObject', '0:MyVariable'])
            obj_cloud = await client_cloud.nodes.root.get_child(['0:Objects', '0:ExamplePLC', '0:MyObject', '0:MyVariable'])

            for i in range(10):
                await asyncio.sleep(0.1)
                cloud_val = await obj_cloud.get_value()
                PLC_val = await obj_PLC.get_value()
                _logger.info(f"PLC has value {PLC_val} and cloud has value {cloud_val}")
                assert abs(PLC_val - cloud_val) < 0.3


@pytest.mark.asyncio
async def test_forwarding_to_PLC(client_PLC, client_cloud):
    async with client_PLC:
        async with client_cloud:
            obj_PLC = await client_PLC.nodes.root.get_child(['0:Objects', '0:MyObject', '0:MyVariable'])
            obj_cloud = await client_cloud.nodes.root.get_child(['0:Objects', '0:ExamplePLC', '0:MyObject', '0:MyVariable'])
            for i in range(10):
                await obj_cloud.set_value(random.randint(0, 50))
                cloud_val = await obj_cloud.get_value()
                PLC_val = await obj_PLC.get_value()
                _logger.info(f"PLC has value {PLC_val} and cloud has value {cloud_val}")
                assert abs(PLC_val - cloud_val) < 0.3

# async def main():
#
#
#
#     await client_PLC.connect()
#     await client_cloud.connect()
#     obj_PLC = await client_PLC.nodes.root.get_child(['0:Objects', '0:MyObject', '0:MyVariable'])
#     obj_cloud = await client_cloud.nodes.root.get_child(['0:Objects', '0:ExamplePLC', '0:MyObject', '0:MyVariable'])
#
#     for i in range(10):
#         await asyncio.sleep(3)
#         await obj_cloud.set_value(42)
#         cloud_val = await obj_cloud.get_value()
#         PLC_val = await obj_PLC.get_value()
#         _logger.info(f"PLC has value {PLC_val} and cloud has value {cloud_val}")
#         assert abs(PLC_val - cloud_val) < 0.3

if __name__ == '__main__':
    asyncio.run(main())