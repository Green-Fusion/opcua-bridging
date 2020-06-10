import logging
import asyncio

from asyncua import Server, Client

from cloud.node_walking import clone_and_subscribe
from cloud.subscription_handler import SubscriptionHandler
from asyncua.crypto.certificate_handler import CertificateHandler
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256
from asyncua.server.users import UserRole
from asyncua.server.user_managers import CertificateUserManager
from asyncua import ua

logging.basicConfig(level=logging.WARNING)
_logger = logging.getLogger('asyncua')

PLC_url = "opc.tcp://plc:4840/freeopcua/server/"
cloud_url = "opc.tcp://cloud:4840/freeopcua/server/"


async def main():
    # setup our serverclone_and_subscribe(client_node, server_node, sub_handler)
    certificate_handler = CertificateHandler()
    await certificate_handler.trust_certificate('/credentials/user_admin_cert.der', label='user',
                                                user_role=UserRole.Admin)

    server = Server(user_manager=CertificateUserManager(certificate_handler))
    await server.init()
    server.set_endpoint(cloud_url)
    server.set_security_policy([ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt],
                               certificate_handler=certificate_handler)

    await server.load_certificate("/credentials/cloud_cert.der")
    await server.load_private_key("/credentials/cloud_private_key.pem")


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
    handler = SubscriptionHandler(client, server)

    subscription = await client.create_subscription(5, handler)

    await clone_and_subscribe(node_1_client, obj_1, handler, subscription, client)
    await clone_and_subscribe(node_2_client, obj_2, handler, subscription, client)
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
