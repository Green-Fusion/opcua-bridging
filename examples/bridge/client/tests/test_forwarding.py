import logging
import asyncio

from asyncua import Client
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256
import pytest
from asyncua.ua.uaerrors import BadInvalidArgument
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
        certificate='/credentials/user_admin_cert.der',
        private_key='/credentials/user_admin_private_key.pem',
        server_certificate='/credentials/PLC_cert.der'
    )
    return client_PLC


@pytest.fixture()
async def client_cloud():
    client_cloud = Client(url=cloud_url)
    await client_cloud.set_security(
        SecurityPolicyBasic256Sha256,
        certificate='/credentials/user_admin_cert.der',
        private_key='/credentials/user_admin_private_key.pem',
        server_certificate='/credentials/cloud_cert.der'
    )
    return client_cloud


@pytest.mark.asyncio
async def test_forwarding_from_plc(client_PLC, client_cloud):
    async with client_PLC:
        async with client_cloud:
            obj_PLC = await client_PLC.nodes.root.get_child(['0:Objects', '0:MyObject', '0:MyVariable'])
            obj_cloud = await client_cloud.nodes.root.get_child(['0:Objects', '0:plc_1', "0:Objects",
                                                                 "0:MyObject", "0:MyVariable"])

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
            obj_cloud = await client_cloud.nodes.root.get_child(['0:Objects', '0:plc_1', "0:Objects",
                                                                 "0:MyObject", "0:MyVariable"])
            _logger.warning(await obj_cloud.get_value())
            for i in range(10):
                randint = random.randint(0, 50)
                _logger.warning(randint)
                await obj_cloud.set_value(randint)
                cloud_set_immediate_val = await obj_cloud.get_value()
                await asyncio.sleep(0.5)
                cloud_val = await obj_cloud.get_value()
                PLC_val = await obj_PLC.get_value()
                _logger.info(f"PLC has value {PLC_val} and cloud has value {cloud_val}")
                allowance = 0.3
                # if this fails then the client didnt write to cloud
                assert abs(cloud_set_immediate_val - randint) < allowance
                # if this fails then that write wasnt forwarded.
                assert abs(PLC_val - cloud_val) < allowance


@pytest.mark.asyncio
async def test_function_forwarding(client_cloud: Client):
    async with client_cloud:
        func_node = await client_cloud.nodes.root.get_child(['0:Objects', '0:plc_1', '0:Objects', '0:Controlling', '0:mymethod'])
        out = await client_cloud.nodes.server.call_method(func_node.nodeid, 6)
        assert out is True

        out = await client_cloud.nodes.server.call_method(func_node.nodeid, 1)
        assert out is False

        with pytest.raises(BadInvalidArgument):
            out3 = await client_cloud.nodes.server.call_method(func_node.nodeid, 'hello')
