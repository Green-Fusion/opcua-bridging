import logging
from asyncua import ua
from asyncua.ua.uatypes import VariantType
from asyncua.ua.uaprotocol_auto import NodeClass
from asyncua.ua.uaerrors import BadOutOfService, BadAttributeIdInvalid
import datetime

_logger = logging.getLogger('asyncua')


async def browse_nodes(node, to_export=False):
    """
    Build a nested node tree dict by recursion (filtered by OPC UA objects and variables).
    """
    _logger.warning(node.nodeid.to_string())
    node_class = await node.read_node_class()
    children = []
    for child in await node.get_children():
        if await child.read_node_class() in [ua.NodeClass.Object, ua.NodeClass.Variable]:
            children.append(
                await browse_nodes(child, to_export=to_export)
            )
    if node_class != ua.NodeClass.Variable:
        var_type = None
    else:
        try:
            var_type = (await node.read_data_type_as_variant_type()).value
        except ua.UaError:
            _logger.warning('Node Variable Type could not be determined for %r', node)
            var_type = None
    output = {
        'id': node.nodeid.to_string(),
        'name': (await node.read_display_name()).Text,
        'cls': node_class.value,
        'type': var_type,
    }

    if not to_export:
        output['node'] = node
        output['children'] = children
    else:
        if len(children) != 0:
            output['children'] = children
        if output['type']:
            output['type'] = VariantType(output['type'])
        if output['cls']:
            output['cls'] = NodeClass(output['cls']).name
        if output['cls'] == 'Variable':
            try:
                output['current_value'] = await node.get_value()
            except (BadOutOfService, BadAttributeIdInvalid):
                output['current_value'] = None
    return output


async def clone_nodes(nodes_dict, base_object, idx=0):
    mapping_list = []
    if nodes_dict['cls'] == 1:
        # node is an object
        next_obj = await base_object.add_object(idx, nodes_dict['name'])
        for child in nodes_dict['children']:
            mapping_list.extend(await clone_nodes(child, next_obj, idx=idx))
    elif nodes_dict['cls'] == 2:
        # node is a variable
        next_var = await add_variable(base_object, idx, nodes_dict['name'], nodes_dict['type'])
        mapped_id = next_var.nodeid.to_string()
        mapping_list.append((nodes_dict['id'], mapped_id))
    else:
        raise NotImplementedError
    return mapping_list


async def add_variable(base_object, idx, node_name, node_type):
    if node_type == VariantType.Boolean:
        default_val = False
    elif node_type in [VariantType.Int16, VariantType.UInt16, VariantType.Int32, VariantType.UInt32, VariantType.Int64, VariantType.UInt64]:
        default_val = 0
    elif node_type == VariantType.String:
        default_val = ''
    elif node_type == VariantType.DateTime:
        default_val = datetime.datetime(seconds=0)
    else:
        default_val = None
    await base_object.add_variable(idx, node_name, default_val, node_type)
