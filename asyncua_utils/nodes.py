import logging
import asyncua
from asyncua import ua, Node, Client, Server
from asyncua.ua.uatypes import VariantType, NodeId
from asyncua.ua.uaprotocol_auto import NodeClass, Argument
from asyncua.ua.uaerrors import BadOutOfService, BadAttributeIdInvalid, BadInternalError, \
                                BadSecurityModeInsufficient, BadNodeIdExists, UaError
import asyncio
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

    node_children = await node.get_children()
    for child in node_children:
        if await child.read_node_class() in [ua.NodeClass.Object, ua.NodeClass.Variable, ua.NodeClass.Method]:
            children.append(
                await browse_nodes(child, to_export=to_export, path=deepcopy(path))
            )
    if node_class == ua.NodeClass.Object:
        var_type = None
    elif node_class == ua.NodeClass.Method:
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
            extension_dict = handle_asyncua_saving(output['current_value'])
            output['extension_object'] = extension_dict
            # if the current value is an asyncua object, which isnt yaml'd easily
            del output['current_value']

    return output


def handle_asyncua_saving(node_value):
    if isinstance(node_value, list) and all(isinstance(sub_val, Argument) for sub_val in node_value):
        return [
                {
                    'Type': 'argument',
                    'Name': sub_val.Name,
                    'DataType': sub_val.DataType.to_string(),
                    'ValueRank': sub_val.ValueRank,
                    'ArrayDimensions': sub_val.ArrayDimensions,
                    'Description': sub_val.Description.to_string()
                 }
                for sub_val in node_value
            ]
    else:
        _logger.warning(f'node value {node_value} not yet supported')
        return None


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


async def clone_nodes(nodes_dict: dict, base_object: Node, client_namespace_array: list, server: Server,
                      method_forwarding=None):
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
                mapping_list.extend(await clone_nodes(child, next_obj, client_namespace_array, server, method_forwarding))
        else:
            return mapping_list
    elif nodes_dict['cls'] in [2, 'Variable']:
        # node is a variable
        next_var = await add_variable(base_object, nodes_dict, node_id)
        if next_var is None:
            return mapping_list
        mapped_id = next_var.nodeid.to_string()
        mapping_list.append((nodes_dict['id'], mapped_id))
    elif nodes_dict['cls'] in [4, 'Method']:
        await method_forwarding.make_function_link(node_id, base_object, nodes_dict)
        return mapping_list
    else:
        _logger.warning(nodes_dict['cls'])
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

    if node_type in [VariantType.ExtensionObject, VariantType.Variant]:
        return None
    elif node_dict.get('current_value'):
        original_val = node_dict['current_value']
    elif node_type in [VariantType.Boolean]:
        original_val = False
    elif node_type in [VariantType.Int16, VariantType.UInt16,
                       VariantType.Int32, VariantType.UInt32,
                       VariantType.Int64, VariantType.UInt64,
                       VariantType.Float, VariantType.Double]:
        original_val = 0
    elif node_type in [VariantType.String, VariantType.LocalizedText, VariantType.Byte]:
        original_val = ''
    elif node_type == VariantType.DateTime:
        original_val = datetime.datetime.today()
    else:
        _logger.warning(f"node type {node_type} not covered by add_variable")
        original_val = 0.0

    return await base_object.add_variable(node_id, node_name, original_val, node_type)


def extract_node_id(node_id_str):
    regex_string = "i=(\d*)"
    int_matches = re.findall(regex_string, node_id_str)
    if len(int_matches) == 1:
        return int(int_matches[0])
    else:
        raise NotImplementedError