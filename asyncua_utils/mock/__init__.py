import logging
import asyncua
from asyncua import ua, Node, Server
from asyncua.ua.uatypes import VariantType, NodeId, LocalizedText, StatusCode
from asyncua.ua.uaprotocol_auto import NodeClass, Argument
from asyncua.ua.uaerrors import BadOutOfService, BadAttributeIdInvalid, BadInternalError, \
                                BadSecurityModeInsufficient, BadNodeIdExists, UaError, \
                                BadBrowseNameDuplicated
from asyncua.ua.status_codes import StatusCodes
import datetime
from copy import deepcopy
import re
from typing import Union
import uuid

from asyncua_utils.node_utils import extract_node_id
from asyncua_utils.nodes import add_variable

_logger = logging.getLogger('asyncua')

async def clone_nodes(nodes_dict: dict, base_object: Node, server: Server):
    mapping_list = []
    node_id = nodes_dict['id']  # generate a nodeid to avoid collisions.

    if nodes_dict['cls'] in [1, 'Object']:
        # node is an object
        try:
            node_type = nodes_dict.get('type_definition')
            if extract_node_id(node_type) == ua.object_ids.ObjectIds.FolderType:
                # folder has to be added as folder
                next_obj = await base_object.add_object(node_id, nodes_dict['name'],
                                                        objecttype=node_type)
            else:
                next_obj = await base_object.add_object(node_id, nodes_dict['name'],
                                                        objecttype=None)

                if node_type:
                    # we do this, otherwise a load of junk gets added.
                    await next_obj.add_reference(node_type, reftype='i=40')
                    await next_obj.delete_reference(ua.object_ids.ObjectIds.BaseObjectType, reftype='i=40')

        except (BadNodeIdExists, BadBrowseNameDuplicated) as e:
            _logger.warning(f'duplicate node {nodes_dict["name"]}')
            return mapping_list
        except RuntimeError as e:
            # TODO: deal with node types which are inherited
            _logger.warning(e)
            _logger.warning(f'node type {node_type} not supported')
            try:
                next_obj = await base_object.get_child(nodes_dict['name'])
            except ua.uaerrors.BadNoMatch:
                next_obj = await base_object.add_object(node_id, nodes_dict['name'],
                                                        objecttype=None)

        mapping_list.append({'original_id': nodes_dict['id'], 'mapped_id': next_obj.nodeid.to_string(),
                             'type': 'Object', 'references': nodes_dict['references']})
        if nodes_dict.get('children'):
            for child in nodes_dict['children']:
                mapping_list.extend(await clone_nodes(child, next_obj, server))
        else:
            return mapping_list
    elif nodes_dict['cls'] in [2, 'Variable']:
        # node is a variable
        next_obj = await add_variable(base_object, nodes_dict, node_id)
        if next_obj is None:
            return mapping_list
        mapped_id = next_obj.nodeid.to_string()
        mapping_list.append({'original_id': nodes_dict['id'], 'mapped_id': mapped_id, 'type': 'Variable',
                             'references': nodes_dict['references']})
        if nodes_dict.get('children'):
            for child in nodes_dict['children']:
                mapping_list.extend(await clone_nodes(child, next_obj, server))
        else:
            return mapping_list
    # elif nodes_dict['cls'] in [4, 'Method']:
    #     mapped_node_id = await method_forwarding.make_function_link(node_id, base_object, nodes_dict)
    #     mapping_list.append({'original_id': nodes_dict['id'], 'mapped_id': mapped_node_id.to_string(), 'type': 'Method',
    #                          'references': nodes_dict['references']})
    #     return mapping_list
    else:
        _logger.warning(nodes_dict['cls'])
        raise NotImplementedError
    return mapping_list

