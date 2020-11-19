import logging
import asyncua
from asyncua import ua, Node, Client, Server
from asyncua.ua.uatypes import VariantType, NodeId
from asyncua.ua.uaprotocol_auto import NodeClass
from asyncua.ua.uaerrors import BadOutOfService, BadAttributeIdInvalid, BadInternalError, \
                                BadSecurityModeInsufficient, BadNodeIdExists, UaError
import datetime
from copy import deepcopy
import re
from typing import Union

_logger = logging.getLogger('asyncua')


async def browse_nodes(node, to_export=False, path=None):
    """
    Build a nested node tree dict by recursion (filtered by OPC UA objects and variables).
    """
    node_id = node.nodeid.to_string()
    node_class = await node.read_node_class()
    children = []
    node_name = (await node.read_browse_name()).to_string()

    if path is None:
        path = [node_name]
    else:
        path.append(node_name)

    for child in await node.get_children():
        if await child.read_node_class() in [ua.NodeClass.Object, ua.NodeClass.Variable]:
            children.append(
                await browse_nodes(child, to_export=to_export, path=deepcopy(path))
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
        except (BadOutOfService, BadAttributeIdInvalid, BadInternalError, BadSecurityModeInsufficient, UaError):
            current_value = None
    output = {
        'id': node_id,
        'name': node_name,
        'cls': node_class.value,
        'type': var_type,
        'path': deepcopy(path)
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
        else:
            del output['type']
        if output['cls']:
            output['cls'] = NodeClass(output['cls']).name
        if output.get('current_value') and check_if_object_is_from_module(output['current_value'], asyncua):
            # if the current value is an asyncua object, which isnt yaml'd easily
            del output['current_value']

    return output


def check_if_object_is_from_module(obj_val, module):
    """
    function to see if the variable is an object that comes from the module, or any of its constituent parts are.
    :param obj_val:
    :param module:
    :return:
    """
    if isinstance(obj_val, list):
        return any(check_if_object_is_from_module(val, module) for val in obj_val)
    elif isinstance(obj_val, dict):
        return any(check_if_object_is_from_module(val, module) for val in obj_val.values())
    else:
        return getattr(obj_val, '__module__', '').startswith(module.__name__)


async def clone_nodes(nodes_dict: dict, base_object: Node, client_namespace_array: list, server: Server):
    mapping_list = []
    node_id = NodeId()  # generate a nodeid to avoid collisions.
    nodes_dict['name'], namespace_idx = await fix_name_and_get_namespace(nodes_dict['name'], client_namespace_array,
                                                                         server)

    if nodes_dict['cls'] in [1, 'Object']:
        # node is an object

        if nodes_dict.get('children'):
            try:
                next_obj = await base_object.add_object(node_id, nodes_dict['name'])
            except BadNodeIdExists as e:
                _logger.warning(f'duplicate node {nodes_dict["name"]}')
                return mapping_list
            for child in nodes_dict['children']:
                mapping_list.extend(await clone_nodes(child, next_obj, client_namespace_array, server))
        else:
            return mapping_list
    elif nodes_dict['cls'] in [2, 'Variable']:
        # node is a variable
        next_var = await add_variable(base_object, nodes_dict, node_id)
        if next_var is None:
            return mapping_list
        mapped_id = next_var.nodeid.to_string()
        mapping_list.append((nodes_dict['id'], mapped_id))
    else:
        raise NotImplementedError
    return mapping_list


async def fix_name_and_get_namespace(name: str, namespace_array: list, server: Server):
    if name.startswith('http://'):
        _logger.warning('urls as names do not work, stripping the http')
        name = name[len('http://'):]
    if re.search(r"^\d:", name):
        namespace_idx = int(name[0])
        namespace_uri = namespace_array[namespace_idx]
        namespace_id = await server.register_namespace(namespace_uri)
    else:
        raise KeyError
    return name, namespace_id


async def add_variable(base_object: Node, node_dict: dict, node_id: Union[str, NodeId]):
    node_name = node_dict['name']
    node_type = node_dict.get('type')

    if isinstance(node_type, str):
        node_type = VariantType[node_type]

    if node_type == VariantType.ExtensionObject:
        _logger.warning(f"Extension Objects are not supported by the bridge. Skipping")
        return None
    elif node_dict.get('current_value'):
        original_val = node_dict['current_value']
    elif node_type in [VariantType.Boolean]:
        original_val = False
    elif node_type in [VariantType.Int16, VariantType.UInt16,
                       VariantType.Int32, VariantType.UInt32,
                       VariantType.Int64, VariantType.UInt64,
                       VariantType.Float]:
        original_val = 0
    elif node_type in [VariantType.String, VariantType.LocalizedText, VariantType.Byte]:
        original_val = ''
    elif node_type == VariantType.DateTime:
        original_val = datetime.datetime.today()
    else:
        _logger.warning(f"node type {node_type} not covered by add_variable")
        original_val = 0.0

    return await base_object.add_variable(node_id, node_name, original_val, node_type)
