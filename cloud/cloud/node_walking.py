import logging
from asyncua import ua

_logger = logging.getLogger('asyncua')


async def browse_nodes(node):
    """
    Build a nested node tree dict by recursion (filtered by OPC UA objects and variables).
    """
    node_class = await node.read_node_class()
    children = []
    for child in await node.get_children():
        if await child.read_node_class() in [ua.NodeClass.Object, ua.NodeClass.Variable]:
            children.append(
                await browse_nodes(child)
            )
    if node_class != ua.NodeClass.Variable:
        var_type = None
    else:
        try:
            var_type = (await node.read_data_type_as_variant_type()).value
        except ua.UaError:
            _logger.warning('Node Variable Type could not be determined for %r', node)
            var_type = None
    return {
        'id': node.nodeid.to_string(),
        'name': (await node.read_display_name()).Text,
        'cls': node_class.value,
        'children': children,
        'type': var_type,
    }


async def clone_nodes(nodes_dict, base_object, idx=0):
    mapping_list = []
    if nodes_dict['cls'] == 1:
        # node is an object
        next_obj = await base_object.add_object(idx, nodes_dict['name'])
        for child in nodes_dict['children']:
            mapping_list.extend(await clone_nodes(child, next_obj, idx=idx))
    elif nodes_dict['cls'] == 2:
        # node is a variable
        next_var = await base_object.add_variable(idx, nodes_dict['name'], 0.0)
        mapped_id = next_var.nodeid.to_string()
        mapping_list.append((nodes_dict['id'], mapped_id))
    else:
        raise NotImplementedError
    return mapping_list


def subscribe_with_handler_from_list(sub_handler, mapping_list):
    for server_id, client_id in mapping_list:
        sub_handler.add_connection(server_id, client_id)


async def clone_and_subscribe(client_node, server_node, sub_handler):
    node_dict = await browse_nodes(client_node)
    mapping_list = await clone_nodes(node_dict, server_node)
    subscribe_with_handler_from_list(sub_handler, mapping_list)
