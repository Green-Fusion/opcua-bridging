import yaml

from asyncua_utils.nodes import browse_nodes
import logging
import asyncua
from asyncua_utils.bridge.subscription import SubscriptionHandler
from asyncua_utils.bridge import clone_and_subscribe
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256


async def produce_server_dict(client_node):
    node_dict = await browse_nodes(client_node, to_export=True)
    return node_dict


async def cloned_namespace_dict(connection_dict):
    connection_dict['nodes'] = await produce_server_dict(connection_dict['nodes'])
    return connection_dict


async def produce_full_bridge_yaml(connection_list, output_file):
    full_dict = []
    for connection in connection_list:
        full_dict.append(await cloned_namespace_dict(connection))

    yaml.dump(full_dict, open(output_file, 'w'))


async def bridge_from_yaml(server_object, server_yaml_file):
    """

    :param server_object:
    :type server_object: asyncua.Server
    :param server_yaml_file:
    :return:
    """
    specification = yaml.load(open(server_yaml_file, 'r'), Loader=yaml.SafeLoader)
    for namespace in specification:
        namespace_idx = await server_object.register_namespace(namespace['namespace'])
        downstream_client = asyncua.Client(url=namespace['url'])
        if namespace.get('bridge_certificate'):
            await downstream_client.set_security(SecurityPolicyBasic256Sha256,
                                                 certificate_path=namespace['bridge_certificate'],
                                                 private_key_path=namespace['bridge_private_key'],
                                                 server_certificate_path=namespace['server_certificate'])
        await downstream_client.connect()
        sub_handler = SubscriptionHandler(downstream_client, server_object)
        subscription = await downstream_client.create_subscription(5, sub_handler)
        await clone_and_subscribe(downstream_client, namespace['nodes'], f'ns={namespace_idx};',
                                  server_object.nodes.objects, sub_handler, subscription, namespace_idx)
        sub_handler.subscribe_to_writes()