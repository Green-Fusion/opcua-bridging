import logging
from asyncua import ua
from asyncua.ua.uatypes import VariantType
from asyncua.ua.uaprotocol_auto import NodeClass
from asyncua.ua.uaerrors import BadOutOfService, BadAttributeIdInvalid, BadInternalError
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
            var_type = (await node.read_data_type_as_variant_type())
        except ua.UaError:
            _logger.warning('Node Variable Type could not be determined for %r', node)
            var_type = None
        try:
            current_value = await node.get_value()
        except (BadOutOfService, BadAttributeIdInvalid, BadInternalError):
            current_value = None
    output = {
        'id': node.nodeid.to_string(),
        'name': (await node.read_display_name()).Text,
        'cls': node_class.value,
        'type': var_type,
    }
    if var_type:
        output['current_value'] = current_value

    if not to_export:
        output['node'] = node
        output['children'] = children
    else:
        if len(children) != 0:
            output['children'] = children
        if output['type']:
            output['type'] = VariantType(output['type']).name
        if output['cls']:
            output['cls'] = NodeClass(output['cls']).name
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
        next_var = await add_variable(base_object, idx, nodes_dict)
        mapped_id = next_var.nodeid.to_string()
        mapping_list.append((nodes_dict['id'], mapped_id))
    else:
        raise NotImplementedError
    return mapping_list


async def add_variable(base_object, idx, node_dict):
    node_name = node_dict['name']
    node_type = node_dict['type']
    if node_dict.get('current_value'):
        original_val = node_dict['current_value']
    elif node_type == VariantType.Boolean:
        original_val = False
    elif node_type in [VariantType.Int16, VariantType.UInt16, VariantType.Int32,
                       VariantType.UInt32, VariantType.Int64, VariantType.UInt64,
                       VariantType.Float]:
        original_val = 0
    elif node_type in [VariantType.String, VariantType.LocalizedText, VariantType.Byte]:
        original_val = ''
    elif node_type == VariantType.DateTime:
        original_val = datetime.datetime(seconds=0)
    else:
        _logger.warning(f"node type {node_type} not covered by add_variable")
        original_val = 0.0
    return await base_object.add_variable(idx, node_name, original_val, node_type)
