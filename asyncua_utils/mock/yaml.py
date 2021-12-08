from asyncua_utils.mock import clone_nodes
import yaml
import logging


async def mock_opcua_server_from_yaml(server_object, server_yaml_file):
    specification = yaml.load(open(server_yaml_file, 'r'), Loader=yaml.SafeLoader)
    logging.info('specification yaml loaded')
    sub_list = []
    # initial_nodes = get_nodeid_list(server_object.iserver.aspace)  # needed to initialize DownstreamBridgeNodeMapping
    for downstream_opc_server in specification:
        logging.info('subscription created')
        base_object = server_object.nodes.objects
        logging.info('node clone beginning')
        node_mapping_list = await clone_nodes(downstream_opc_server['nodes'], base_object, server_object)
        # logging.info('reference applying')
        # await apply_references(server_object, node_mapping_list, node_mapping)
        logging.info('node clone finished')
    return sub_list