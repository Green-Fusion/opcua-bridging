import yaml

from asyncua_utils.nodes import browse_nodes
import logging
import asyncua
from asyncua import Server, Client
from asyncua.ua.uatypes import NodeId
from asyncua_utils.bridge.subscription import SubscriptionHandler
from asyncua_utils.bridge.node_mapping import DownstreamBridgeNodeMapping
from asyncua_utils.bridge.alarms import AlarmHandler
from asyncua_utils.bridge import clone_and_subscribe
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256
from asyncua_utils.bridge.method_forwarding import MethodForwardingHandler
from asyncua_utils.node_utils import extract_node_id
from asyncua.server.address_space import AddressSpace
from asyncua import ua
from tqdm import tqdm


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


async def add_server_as_notifier(downstream_server: Client, bridge_server: Server,
                                 node_mapping: DownstreamBridgeNodeMapping):
    downstream_server_node_id = node_mapping.get_bridge_id(downstream_server.nodes.server.nodeid.to_string())
    await bridge_server.nodes.server.add_reference(downstream_server_node_id,
                                                   reftype=asyncua.ua.ObjectIds.HasNotifier)


def get_nodeid_list(aspace: AddressSpace):
    aspace_list = [a.to_string() for a in aspace.keys()]
    return aspace_list


async def bridge_from_yaml(server_object, server_yaml_file):
    """

    :param server_object:
    :type server_object: asyncua.Server
    :param server_yaml_file:
    :return:
    """
    specification = yaml.load(open(server_yaml_file, 'r'), Loader=yaml.SafeLoader)
    sub_list = []
    initial_nodes = get_nodeid_list(server_object.iserver.aspace)  # needed to initialize DownstreamBridgeNodeMapping
    for downstream_opc_server in specification:
        downstream_client = asyncua.Client(url=downstream_opc_server['url'])
        if downstream_opc_server.get('bridge_certificate'):
            await downstream_client.set_security(SecurityPolicyBasic256Sha256,
                                                 certificate=downstream_opc_server['bridge_certificate'],
                                                 private_key=downstream_opc_server['bridge_private_key'],
                                                 server_certificate=downstream_opc_server['server_certificate'])
        await downstream_client.connect()
        node_mapping = DownstreamBridgeNodeMapping(initial_nodes)
        sub_handler = SubscriptionHandler(downstream_client, server_object, node_mapping)
        method_handler = MethodForwardingHandler(downstream_client, server_object, node_mapping)
        subscription = await downstream_client.create_subscription(5, sub_handler)
        await subscription.subscribe_events(downstream_client.nodes.server, ua.ObjectIds.OffNormalAlarmType)
        base_object = await server_object.nodes.objects.add_object(NodeId(), downstream_opc_server['name'])
        node_mapping_list = await clone_and_subscribe(downstream_client, downstream_opc_server['nodes'],
                                  base_object, sub_handler, subscription, server_object, method_handler)
        await apply_references(server_object, node_mapping_list, node_mapping)
        sub_handler.subscribe_to_writes()
        await sub_handler.start(subscription.subscription_id)
        sub_list.append({'sub_handler': sub_handler, 'subscription': subscription,
                         'downstream_client': downstream_client, 'node_mapping': node_mapping})
    return sub_list


async def apply_references(server: Server, node_mapping_list: list, node_mapping: DownstreamBridgeNodeMapping):
    for node_dict in tqdm(node_mapping_list):
        references = node_dict['references']
        original_node = server.get_node(node_dict['mapped_id'])
        for ref in references:
            new_target = node_mapping.get_bridge_id(ref['target'])
            if new_target is not None:
                try:
                    if ref['refTypeId'] == asyncua.ua.object_ids.ObjectIds.HasTypeDefinition:
                        continue
                    await original_node.add_reference(target=new_target, reftype=ref['refTypeId'],
                                            forward=ref['isForward'])
                except:
                    pass
