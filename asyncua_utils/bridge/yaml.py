import yaml

from asyncua_utils.nodes import browse_nodes
import logging


async def produce_server_dict(client_node):
    node_dict = await browse_nodes(client_node, to_export=True)
    return node_dict


async def cloned_namespace_dict(client_node, namespace, url):
    return {
        'nodes': await produce_server_dict(client_node),
        'namespace': namespace,
        'url': url
    }


async def produce_full_bridge_yaml(connection_list, output_file):
    full_dict = []
    for connection in connection_list:
        full_dict.append(await cloned_namespace_dict(connection['nodes'], connection['namespace'], connection['url']))

    yaml.dump(full_dict, open(output_file, 'w'))
    logging.warning(yaml.dump(full_dict))
